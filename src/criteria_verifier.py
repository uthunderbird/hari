import asyncio
import json
import logging
import random
from base64 import b64encode
from pathlib import Path

from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from models.criteria_verification import Criteria, BulkCvCriteriaMatch, Vacancy
from models.verified_cv import ProbablyCVWithRawText
from output_handler import Attachment
from prompts.verifier_prompt import CRITERIA_VERIFIER_SYSTEM_PROMPT


async def verify_pack(
    cv_pack: list[tuple[str, ProbablyCVWithRawText]],
    vacancy: Vacancy,
    top_n: int = 10,
) -> BulkCvCriteriaMatch:
    model = ChatOpenAI(model="gpt-4o").with_structured_output(BulkCvCriteriaMatch)
    system_prompt = CRITERIA_VERIFIER_SYSTEM_PROMPT.format(
        criteria_list=','.join(str(criteria.model_dump()) for criteria in vacancy.criteria_list),
        vacancy_text=vacancy.text,
        top_n=len(cv_pack),
    )
    user_prompt = json.dumps([{file_path: cv.model_dump()} for file_path, cv in cv_pack], ensure_ascii=False)
    try:
        result: BulkCvCriteriaMatch = await model.ainvoke(
            [
                ('system', system_prompt),
                ('user', user_prompt),
            ]
        )
    except ValidationError:
        # naive retry
        result: BulkCvCriteriaMatch = await model.ainvoke(
            [
                ('system', system_prompt),
                ('user', user_prompt),
            ]
        )
    result.matches = sorted(result.matches, key=lambda x: -x.matching_rate)[:top_n]
    return result

@chain
async def verify_round(
    input_: dict,
):
    vacancy: Vacancy = input_['vacancy']
    cvs: dict[str, ProbablyCVWithRawText] = input_['cvs']
    cvs_per_pack: int = input_['cvs_per_pack']
    top_n_per_pack: int = input_['top_n_per_pack']
    finalize_on: int = input_['finalize_on']
    participants = list(cvs.items())
    random.shuffle(participants)

    round_no = 1

    final_cvs = []

    while len(participants) > finalize_on * 2:
        final_cvs = []
        yield f"Round #{round_no}: {len(participants)} participants in the game.\n"
        packs_amount = len(participants) / cvs_per_pack
        winners = []
        tasks = []
        # Break CVs into packs
        for i in range(0, len(participants), cvs_per_pack):
            pack = participants[i:i + cvs_per_pack]

            # Verify each pack and get top N CVs
            tasks.append(
                asyncio.create_task(
                    verify_pack(
                        cv_pack=pack,
                        vacancy=vacancy,
                        top_n=top_n_per_pack if packs_amount > 1 else finalize_on,
                    )
                )
            )
        task_results = await asyncio.gather(*tasks)
        for top_cvs in task_results:
            # Add top CVs to the total selected list
            for match in top_cvs.matches:
                if match.file_path not in cvs:
                    logging.warning(f"We've lost some CV: `{match.file_path}`")
                    continue
                winners.append((match.file_path, cvs[match.file_path]))
                final_cvs.append(match)
        participants = winners
        round_no += 1
    result = sorted(final_cvs, key=lambda x: -x.matching_rate)[:finalize_on]
    for resume in result:
        file_path = Path(resume.file_path)
        if file_path.suffix == '.pdf':
            mimetype = 'application/pdf'
        elif file_path.suffix == '.docx':
            mimetype = 'application/msword'
        else:
            raise ValueError(f"Unknown exception of a file `{file_path}`")
        yield Attachment(type=mimetype, name=file_path.name, data=b64encode(file_path.read_bytes()).decode())

if __name__ == '__main__':
    from cv_validator import validate_cvs
    from doc_parser import parse_directory
    path = '../cvs'
    test_pack = validate_cvs(
        directory_parser=parse_directory,
        path=path,
    )
    test_vacancy = Vacancy(language='Russian', plan='1. Introduction: Provide a brief overview of the company and its industry.\n2. Responsibilities:\n   - Develop, support, and optimize interfaces for web applications and corporate platforms.\n   - Collaborate closely with designers and backend developers to ensure product functionality and visual aspects.\n   - Participate in architectural discussions and create UX/UI solutions that meet client requirements.\n   - Implement adaptive layouts for various devices and ensure cross-browser compatibility.\n   - Optimize frontend performance for smooth user interaction.\n3. Requirements:\n   - Minimum of 3 years experience as a Frontend Developer using React.\n   - Proficient in JavaScript, HTML, CSS; experience with modern JavaScript frameworks (React, Vue, or similar).\n   - Knowledge of version control systems like Git.\n   - Experience in creating adaptive and cross-browser interfaces.\n   - Understanding of UI/UX principles and experience with API interactions and RESTful services.\n   - Basic understanding of testing tools (JIRA, Trello) and knowledge of database fundamentals.\n4. Conditions:\n   - Convenient office located in the center of Almaty with relaxation areas.\n   - Complimentary coffee and hookah in the office.\n   - Access to a gym during lunch hours.\n   - Flexible working conditions: primarily office-based with occasional remote work.\n   - Periodic treats of fruits and soft drinks.', text='Обязанности:\n  Разработка, поддержка и оптимизация интерфейсов для веб-приложений и корпоративных платформ.\n  Тесная работа с дизайнерами и бэкенд-разработчиками для обеспечения функциональности и визуальной составляющей продуктов.\n  Участие в архитектурных обсуждениях и создание UX/UI решений, соответствующих требованиям клиентов.\n  Реализация адаптивной верстки для различных устройств, поддержка кросс-браузерной совместимости.\n  Оптимизация производительности фронтенд-части для плавного взаимодействия пользователей с продуктом.\nТребования:\n  Опыт работы на позиции Frontend-разработчика не менее 3 лет на React.\n  Уверенные знания JavaScript, HTML, CSS; опыт работы с современными JavaScript-фреймворками (React, Vue или аналогичными).\n  Знания по работе с системой контроля версий Git.\n  Опыт создания адаптивных и кросс-браузерных интерфейсов.\n  Понимание принципов UI/UX, опыт взаимодействия с API и основ работы RESTful сервисов.\n  Базовое понимание работы с инструментами для тестирования (JIRA, Trello) и знание основ работы с базами данных.\nУсловия:\n  Удобный офис в центре Алматы с зонами для отдыха.\n  Бесплатные кофе и кальян в офисе.\n  Возможность посещения тренажерного зала в обеденное время.\n  Гибкие условия работы: основной формат – работа в офисе, но периодически возможна работа из дома.\n  Периодические угощения фруктами и прохладительными напитками.', criteria_list=[Criteria(short_name='Frontend Development Experience', description='Minimum of 3 years experience as a Frontend Developer using React.', is_mandatory=True), Criteria(short_name='JavaScript, HTML, CSS Skills', description='Proficient in JavaScript, HTML, CSS; experience with modern JavaScript frameworks (React, Vue, or similar).', is_mandatory=True), Criteria(short_name='Version Control Knowledge', description='Knowledge of version control systems like Git.', is_mandatory=True), Criteria(short_name='Adaptive and Cross-browser Interfaces', description='Experience in creating adaptive and cross-browser interfaces.', is_mandatory=True), Criteria(short_name='UI/UX Principles Understanding', description='Understanding of UI/UX principles and experience with API interactions and RESTful services.', is_mandatory=True), Criteria(short_name='Testing Tools Understanding', description='Basic understanding of testing tools (JIRA, Trello) and knowledge of database fundamentals.', is_mandatory=True)])


    result = asyncio.run(verify_round(
        vacancy=test_vacancy,
        cvs=test_pack,
        cvs_per_pack=13,
        top_n_per_pack=3,
        finalize_on=5,
    ))
    pass
