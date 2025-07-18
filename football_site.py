import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.markdown(
    '''
    <style>
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6;
            padding: 10px 20px;
            margin-right: 5px;
            border-radius: 10px 10px 0 0;
            border: 1px solid #ccc;
            font-weight: 500;
        }
        .stTabs [aria-selected="true"] {
            background-color: #ffffff;
            border-bottom: 2px solid #ff4b4b;
            color: black;
        }
    </style>
    ''',
    unsafe_allow_html=True
)


# Верхнее меню для выбора страницы
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Чемпионат", "Кубок", "Составы команд", "Статистика", "Анонс тура"])

with tab1:  # Чемпионат
    col1, col2 = st.columns([1, 8])
    with col2:
        st.title("🏆 Чемпионат Волжского района по футболу 2025 года")

    # Чтение данных
    matches = pd.read_csv("matches.csv", encoding='utf-8-sig', na_values=['', ' '])
    df_schedule = pd.read_csv("schedule.csv", encoding='utf-8-sig')

    # Обработка данных и турнирная таблица (остается без изменений)
    matches["Голы хозяев"] = pd.to_numeric(matches["Голы хозяев"], errors='coerce')
    matches["Голы гостей"] = pd.to_numeric(matches["Голы гостей"], errors='coerce')

    teams = pd.unique(matches[["Хозяева", "Гости"]].values.ravel())
    stats = {team: {"Игры": 0, "Победы": 0, "Ничьи": 0, "Поражения": 0,
                    "Забито": 0, "Пропущено": 0, "Очки": 0} for team in teams}

    for _, row in matches.iterrows():
        home, away = row["Хозяева"], row["Гости"]
        hg, ag = row["Голы хозяев"], row["Голы гостей"]

        if pd.isna(hg) or pd.isna(ag):
            continue

        try:
            hg = int(hg) if not pd.isna(hg) else 0
            ag = int(ag) if not pd.isna(ag) else 0
        except (ValueError, TypeError):
            continue

        stats[home]["Игры"] += 1
        stats[away]["Игры"] += 1
        stats[home]["Забито"] += hg
        stats[home]["Пропущено"] += ag
        stats[away]["Забито"] += ag
        stats[away]["Пропущено"] += hg

        if hg > ag:
            stats[home]["Победы"] += 1
            stats[away]["Поражения"] += 1
            stats[home]["Очки"] += 3
        elif hg < ag:
            stats[away]["Победы"] += 1
            stats[home]["Поражения"] += 1
            stats[away]["Очки"] += 3
        else:
            stats[home]["Ничьи"] += 1
            stats[away]["Ничьи"] += 1
            stats[home]["Очки"] += 1
            stats[away]["Очки"] += 1

    table_data = []
    for team, s in stats.items():
        table_data.append({
            "Команда": team,
            "Игры": int(s["Игры"]),
            "Победы": int(s["Победы"]),
            "Ничьи": int(s["Ничьи"]),
            "Поражения": int(s["Поражения"]),
            "Забито": int(s["Забито"]),
            "Пропущено": int(s["Пропущено"]),
            "Разница мячей": int(s["Забито"]) - int(s["Пропущено"]),
            "Очки": int(s["Очки"])
        })

    df = pd.DataFrame(table_data)
    df = df.sort_values(by=["Очки", "Разница мячей"], ascending=[False, False]).reset_index(drop=True)
    df.insert(0, "№", range(1, len(df) + 1))

    cols = ["№", "Команда", "Игры", "Победы", "Ничьи", "Поражения", "Забито", "Пропущено", "Разница мячей", "Очки"]
    df = df[cols]

    st.subheader("📊 Турнирная таблица")
    st.dataframe(df, use_container_width=True)

    st.subheader("🎯 Результаты матчей")
    played_matches = matches[
        (~matches["Голы хозяев"].isna() & ~matches["Голы гостей"].isna()) &
        ((matches["Голы хозяев"] != 0) | (matches["Голы гостей"] != 0))
        ]

    played_rounds = sorted(played_matches["Тур"].unique())

    if played_rounds:
        selected_round = st.selectbox(
        "Выберите тур",
        played_rounds,
        index=len(played_rounds) - 1
    )
        round_matches = matches[matches["Тур"] == selected_round].copy()


        def format_result(row):
            if pd.isna(row['Голы хозяев']) or pd.isna(row['Голы гостей']):
                return "Не сыграно"
            try:
                return f"{int(row['Голы хозяев'])}:{int(row['Голы гостей'])}"
            except (ValueError, TypeError):
                return "Не сыграно"


        round_matches["Результат"] = round_matches.apply(format_result, axis=1)

        st.dataframe(
            round_matches[["Хозяева", "Гости", "Результат"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Хозяева": "Хозяева",
                "Гости": "Гости",
                "Результат": st.column_config.TextColumn("Результат")
            }
        )

        # Добавленная секция: Статистика по матчу (этот блок был пропущен)
        st.subheader("📊 Статистика матча")

        # Фильтруем только сыгранные матчи в выбранном туре
        played_in_round = round_matches[
            (~round_matches["Голы хозяев"].isna()) &
            (~round_matches["Голы гостей"].isna()) &
            ((round_matches["Голы хозяев"] != 0) | (round_matches["Голы гостей"] != 0))
            ]

        if not played_in_round.empty:
            match_list = [f"{row['Хозяева']} - {row['Гости']} ({int(row['Голы хозяев'])}:{int(row['Голы гостей'])})"
                          for _, row in played_in_round.iterrows()]
            selected_match = st.selectbox("Выберите матч для просмотра статистики", match_list)

            # Получаем данные выбранного матча
            selected_match_data = None
            for _, row in played_in_round.iterrows():
                if f"{row['Хозяева']} - {row['Гости']} ({int(row['Голы хозяев'])}:{int(row['Голы гостей'])})" == selected_match:
                    selected_match_data = row
                    break

            if selected_match_data is not None:
                # Загружаем данные о составах команд и статистике матчей
                try:
                    with open('squads.json', 'r', encoding='utf-8') as f:
                        team_squads = json.load(f)
                    with open('match_stats.json', 'r', encoding='utf-8') as f:
                        match_stats = json.load(f)
                except FileNotFoundError as e:
                    st.error(f"Файл не найден: {e}. Статистика по матчу недоступна.")
                    team_squads = {}
                    match_stats = {"matches": []}

                if team_squads:
                    home_team = selected_match_data['Хозяева']
                    away_team = selected_match_data['Гости']
                    match_date = selected_match_data.get('Дата', 'Неизвестная дата')

                    # Находим статистику для текущего матча
                    current_match_stats = None
                    for match in match_stats["matches"]:
                        if (match["home_team"] == home_team and
                                match["away_team"] == away_team and
                                match.get("round") == selected_round):
                            current_match_stats = match
                            break

                    # Создаем вкладки для разных типов статистики
                    tab_goals, tab_yellow, tab_red = st.tabs(["Голы", "Жёлтые карточки", "Красные карточки"])

                    with tab_goals:
                        st.markdown(f"### Голы в матче {home_team} - {away_team}")
                        if current_match_stats and "goals" in current_match_stats and current_match_stats["goals"]:
                            goals_data = []
                            for goal in current_match_stats["goals"]:
                                goals_data.append({
                                    "Команда": goal["team"],
                                    "Игрок": goal["player"],
                                    "Минута": goal["minute"],
                                    "Ассистент": goal.get("assist", "-")
                                })
                            st.dataframe(
                                pd.DataFrame(goals_data),
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info("Нет данных о забитых голах в этом матче")

                    with tab_yellow:
                        st.markdown(f"### Жёлтые карточки в матче {home_team} - {away_team}")
                        if current_match_stats and "yellow_cards" in current_match_stats and current_match_stats[
                            "yellow_cards"]:
                            yellow_data = []
                            for card in current_match_stats["yellow_cards"]:
                                yellow_data.append({
                                    "Команда": card["team"],
                                    "Игрок": card["player"],
                                    "Минута": card["minute"]
                                })
                            st.dataframe(
                                pd.DataFrame(yellow_data),
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info("Нет данных о желтых карточках в этом матче")

                    with tab_red:
                        st.markdown(f"### Красные карточки в матче {home_team} - {away_team}")
                        if current_match_stats and "red_cards" in current_match_stats and current_match_stats[
                            "red_cards"]:
                            red_data = []
                            for card in current_match_stats["red_cards"]:
                                red_data.append({
                                    "Команда": card["team"],
                                    "Игрок": card["player"],
                                    "Минута": card["minute"]
                                })
                            st.dataframe(
                                pd.DataFrame(red_data),
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info("Нет данных о красных карточках в этом матче")
                else:
                    st.warning("Нет данных о составах команд для отображения статистики матча")
        else:
            st.info("В выбранном туре нет сыгранных матчей для отображения статистики")

    st.subheader("🗓 Календарь игр (по турам)")
    df_schedule["Дата"] = pd.to_datetime(df_schedule["Дата"].astype(str) + ".2025", format="%d.%m.%Y", errors="coerce")
    df_schedule["Дата"] = df_schedule["Дата"].dt.strftime("%d.%m.%Y")
    today = pd.to_datetime(datetime.now().date())
    future_rounds = pd.to_datetime(df_schedule["Дата"], format="%d.%m.%Y", errors="coerce")
    default_round = df_schedule.loc[future_rounds >= today, "Тур"].min() if not future_rounds.empty else df_schedule[
        "Тур"].max()
    selected_schedule_round = st.selectbox(
        "Выберите тур для просмотра календаря",
        sorted(df_schedule["Тур"].unique()),
        index=list(sorted(df_schedule["Тур"].unique())).index(default_round),
        key="schedule"
    )
    st.dataframe(df_schedule[df_schedule["Тур"] == selected_schedule_round], use_container_width=True)

with tab2:  # Кубок
    st.title("🥇 Кубок Волжского района по футболу 2025 года")

    st.markdown("""
    <style>
        .cup-header {
            font-size: 22px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 25px;
            margin-bottom: 10px;
            border-bottom: 2px solid #ff4b4b;
            padding-bottom: 5px;
        }
        .cup-row {
            font-size: 16px;
            margin-bottom: 5px;
            padding: 5px;
        }
        .cup-result {
            font-weight: bold;
        }
        .cup-winner {
            color: green;
            font-weight: bold;
        }
        .cup-match {
            display: flex;
            justify-content: space-between;
        }
        .cup-stats-btn {
            margin-left: 10px;
            padding: 2px 8px;
            font-size: 12px;
        }
        .match-stats-container {
            margin-top: 10px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
    </style>
    """, unsafe_allow_html=True)

    # Загрузка данных кубка
    try:
        with open('cup_matches.json', 'r', encoding='utf-8') as f:
            cup_matches = json.load(f)
    except FileNotFoundError:
        st.error("Файл cup_matches.json не найден")
        cup_matches = []

    # Загрузка статистики матчей кубка
    try:
        with open('cup_match_stats.json', 'r', encoding='utf-8') as f:
            cup_match_stats = json.load(f)
    except FileNotFoundError:
        st.warning("Файл cup_match_stats.json не найден. Статистика матчей недоступна.")
        cup_match_stats = {"matches": []}

    # Группировка матчей по стадиям
    from collections import defaultdict

    stages = defaultdict(list)
    for m in cup_matches:
        stages[m["stage"]].append(m)

    # Отображение матчей по стадиям
    for stage in ["1/8 финала", "1/4 финала", "1/2 финала", "Финал"]:
        st.markdown(f'<div class="cup-header">{stage}</div>', unsafe_allow_html=True)
        for m in stages[stage]:
            date = m["date"]
            home = m["home"]
            away = m["away"]
            score = m["score"]

            # Создаем контейнер для матча
            with st.container():
                # Строка с информацией о матче
                col1, col2, col3 = st.columns([2, 5, 2])

                with col1:
                    st.markdown(f'<div>{date}</div>', unsafe_allow_html=True)

                # Форматирование команд и результата
                if score:
                    try:
                        hg, ag = map(int, score.split(":"))
                        if hg > ag:
                            home = f'<span class="cup-winner">{home}</span>'
                        elif ag > hg:
                            away = f'<span class="cup-winner">{away}</span>'
                    except:
                        pass
                    score_html = f'<span class="cup-result">{score}</span>'
                else:
                    score_html = ""

                with col2:
                    st.markdown(f'<div>{home} – {away}</div>', unsafe_allow_html=True)

                with col3:
                    st.markdown(f'<div>{score_html}</div>', unsafe_allow_html=True)

                # Кнопка для просмотра статистики (если матч сыгран)
                if score:
                    # Находим статистику для текущего матча
                    match_stats = None
                    for match in cup_match_stats["matches"]:
                        if (match["home_team"] == m["home"] and
                                match["away_team"] == m["away"] and
                                match["date"] == m["date"]):
                            match_stats = match
                            break

                    if match_stats:
                        # Создаем уникальный ключ для кнопки
                        btn_key = f"stats_btn_{m['home']}_{m['away']}_{m['date']}"

                        # Отображаем кнопку под матчем
                        if st.button("📊 Показать статистику матча", key=btn_key,
                                     help=f"Статистика матча {m['home']} - {m['away']}"):

                            # Контейнер для статистики
                            with st.container():
                                st.markdown('<div class="match-stats-container">', unsafe_allow_html=True)

                                # Создаем вкладки для разных типов статистики
                                tabs = st.tabs(["Голы", "Жёлтые карточки", "Красные карточки"])

                                with tabs[0]:  # Голы
                                    if "goals" in match_stats and match_stats["goals"]:
                                        goals_data = []
                                        for goal in match_stats["goals"]:
                                            goals_data.append({
                                                "Команда": goal["team"],
                                                "Игрок": goal["player"],
                                                "Минута": goal["minute"],
                                                "Ассистент": goal.get("assist", "-")
                                            })
                                        st.dataframe(
                                            pd.DataFrame(goals_data),
                                            use_container_width=True,
                                            hide_index=True
                                        )
                                    else:
                                        st.info("Нет данных о забитых голах в этом матче")

                                with tabs[1]:  # Жёлтые карточки
                                    if "yellow_cards" in match_stats and match_stats["yellow_cards"]:
                                        yellow_data = []
                                        for card in match_stats["yellow_cards"]:
                                            yellow_data.append({
                                                "Команда": card["team"],
                                                "Игрок": card["player"],
                                                "Минута": card["minute"]
                                            })
                                        st.dataframe(
                                            pd.DataFrame(yellow_data),
                                            use_container_width=True,
                                            hide_index=True
                                        )
                                    else:
                                        st.info("Нет данных о желтых карточках в этом матче")

                                with tabs[2]:  # Красные карточки
                                    if "red_cards" in match_stats and match_stats["red_cards"]:
                                        red_data = []
                                        for card in match_stats["red_cards"]:
                                            red_data.append({
                                                "Команда": card["team"],
                                                "Игрок": card["player"],
                                                "Минута": card["minute"]
                                            })
                                        st.dataframe(
                                            pd.DataFrame(red_data),
                                            use_container_width=True,
                                            hide_index=True
                                        )
                                    else:
                                        st.info("Нет данных о красных карточках в этом матче")

                                st.markdown('</div>', unsafe_allow_html=True)

with tab3:  # Составы команд
    st.title("👥 Составы команд")

    # CSS стили (упрощённые)
    st.markdown("""
    <style>
    .team-table {
        font-size: 16px;
        width: 100%;
    }
    .team-table th {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    # Загрузка данных
    try:
        with open('squads.json', 'r', encoding='utf-8') as f:
            team_squads = json.load(f)
    except FileNotFoundError:
        st.error("Файл squads.json не найден")
        team_squads = {}

    # Поиск игроков
    st.subheader("🔍 Поиск игрока")
    search_query = st.text_input("Введите имя игрока", "", key="player_search").lower()

    # Выбор команды
    selected_team = st.selectbox("Выберите команду", sorted(team_squads.keys()))

    # Фильтрация игроков
    players = team_squads.get(selected_team, [])
    if search_query:
        players = [p for p in players if search_query in p["name"].lower()]

    # Отображение состава
    if not players:
        st.warning("Игроки не найдены")
    else:
        # Создаем DataFrame
        df = pd.DataFrame(players)

        # Отображаем таблицу без столбца с фото
        st.dataframe(
            df[['name', 'number', 'position', 'goals', 'assists', 'yellow_cards', 'red_cards']]
            .rename(columns={
                'name': 'Игрок',
                'number': 'Номер',
                'position': 'Позиция',
                'goals': 'Голы',
                'assists': 'Передачи',
                'yellow_cards': 'Жёлтые',
                'red_cards': 'Красные'
            }),
            column_config={
                "Голы": st.column_config.NumberColumn(format="%d"),
                "Передачи": st.column_config.NumberColumn(format="%d"),
                "Жёлтые": st.column_config.NumberColumn(format="%d"),
                "Красные": st.column_config.NumberColumn(format="%d")
            },
            use_container_width=True,
            hide_index=True
        )

    # Кнопки управления
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Добавить команду", type="secondary"):
            st.info("Функция в разработке")

    with col2:
        st.download_button(
            label="📥 Скачать составы (JSON)",
            data=json.dumps(team_squads, ensure_ascii=False, indent=2),
            file_name="squads.json",
            mime="application/json"
        )

with tab4:  # Статистика
    st.title("📊 Статистика игроков")

    # Добавляем выбор типа турнира
    tournament_type = st.radio(
        "Выберите турнир",
        ["Чемпионат", "Кубок"],
        horizontal=True
    )

    if tournament_type == "Чемпионат":
        # Загрузка данных чемпионата
        try:
            with open('squads.json', 'r', encoding='utf-8') as f:
                team_squads = json.load(f)
        except FileNotFoundError:
            st.error("Файл squads.json не найден")
            team_squads = {}

        # Собираем всех игроков
        all_players = []
        for team, players in team_squads.items():
            for player in players:
                player['team'] = team  # Добавляем название команды
                all_players.append(player)

        if not all_players:
            st.info("Пока нет статистики по игрокам")
        else:
            # Создаем DataFrame
            df = pd.DataFrame(all_players)

            # Стили для таблиц
            st.markdown("""
            <style>
            .stat-table {
                margin-bottom: 30px;
            }
            .stat-title {
                font-size: 1.3em;
                color: #2c3e50;
                margin: 25px 0 10px 0;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 5px;
            }
            </style>
            """, unsafe_allow_html=True)

            # Таблица бомбардиров
            st.markdown('<div class="stat-title">🏅 Лучшие бомбардиры (Чемпионат)</div>', unsafe_allow_html=True)
            scorers = df[df['goals'] > 0].sort_values('goals', ascending=False)
            if not scorers.empty:
                st.dataframe(
                    scorers[['name', 'team', 'goals']]
                    .rename(columns={
                        'name': 'Игрок',
                        'team': 'Команда',
                        'goals': 'Голы'
                    }),
                    column_config={
                        "Голы": st.column_config.NumberColumn(format="%d")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Нет данных о забитых голах")

            # Таблица желтых карточек
            st.markdown('<div class="stat-title">🟨 Желтые карточки (Чемпионат)</div>', unsafe_allow_html=True)
            yellow_cards = df[df['yellow_cards'] > 0].sort_values('yellow_cards', ascending=False)
            if not yellow_cards.empty:
                st.dataframe(
                    yellow_cards[['name', 'team', 'yellow_cards']]
                    .rename(columns={
                        'name': 'Игрок',
                        'team': 'Команда',
                        'yellow_cards': 'Жёлтые'
                    }),
                    column_config={
                        "Жёлтые": st.column_config.NumberColumn(format="%d")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Нет данных о желтых карточках")

            # Таблица красных карточек
            st.markdown('<div class="stat-title">🟥 Красные карточки (Чемпионат)</div>', unsafe_allow_html=True)
            red_cards = df[df['red_cards'] > 0].sort_values('red_cards', ascending=False)
            if not red_cards.empty:
                st.dataframe(
                    red_cards[['name', 'team', 'red_cards']]
                    .rename(columns={
                        'name': 'Игрок',
                        'team': 'Команда',
                        'red_cards': 'Красные'
                    }),
                    column_config={
                        "Красные": st.column_config.NumberColumn(format="%d")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Нет данных о красных карточках")

    else:  # Кубок
        # Загрузка статистики матчей кубка
        try:
            with open('cup_match_stats.json', 'r', encoding='utf-8') as f:
                cup_match_stats = json.load(f)
        except FileNotFoundError:
            st.error("Файл cup_match_stats.json не найден")
            cup_match_stats = {"matches": []}

        # Собираем статистику по игрокам
        player_stats = defaultdict(lambda: {
            "goals": 0,
            "yellow_cards": 0,
            "red_cards": 0,
            "team": ""
        })

        for match in cup_match_stats["matches"]:
            # Обработка голов
            if "goals" in match:
                for goal in match["goals"]:
                    player = goal["player"]
                    player_stats[player]["goals"] += 1
                    player_stats[player]["team"] = goal["team"]

            # Обработка желтых карточек
            if "yellow_cards" in match:
                for card in match["yellow_cards"]:
                    player = card["player"]
                    player_stats[player]["yellow_cards"] += 1
                    player_stats[player]["team"] = card["team"]

            # Обработка красных карточек
            if "red_cards" in match:
                for card in match["red_cards"]:
                    player = card["player"]
                    player_stats[player]["red_cards"] += 1
                    player_stats[player]["team"] = card["team"]

        # Преобразуем в список словарей
        players_data = []
        for player, stats in player_stats.items():
            players_data.append({
                "name": player,
                "team": stats["team"],
                "goals": stats["goals"],
                "yellow_cards": stats["yellow_cards"],
                "red_cards": stats["red_cards"]
            })

        if not players_data:
            st.info("Нет данных по игрокам в кубке")
        else:
            df_cup = pd.DataFrame(players_data)

            # Таблица бомбардиров кубка
            st.markdown('<div class="stat-title">🏅 Лучшие бомбардиры (Кубок)</div>', unsafe_allow_html=True)
            cup_scorers = df_cup[df_cup['goals'] > 0].sort_values('goals', ascending=False)
            if not cup_scorers.empty:
                st.dataframe(
                    cup_scorers[['name', 'team', 'goals']]
                    .rename(columns={
                        'name': 'Игрок',
                        'team': 'Команда',
                        'goals': 'Голы'
                    }),
                    column_config={
                        "Голы": st.column_config.NumberColumn(format="%d")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Нет данных о забитых голах в кубке")

            # Таблица желтых карточек кубка
            st.markdown('<div class="stat-title">🟨 Желтые карточки (Кубок)</div>', unsafe_allow_html=True)
            cup_yellow = df_cup[df_cup['yellow_cards'] > 0].sort_values('yellow_cards', ascending=False)
            if not cup_yellow.empty:
                st.dataframe(
                    cup_yellow[['name', 'team', 'yellow_cards']]
                    .rename(columns={
                        'name': 'Игрок',
                        'team': 'Команда',
                        'yellow_cards': 'Жёлтые'
                    }),
                    column_config={
                        "Жёлтые": st.column_config.NumberColumn(format="%d")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Нет данных о желтых карточках в кубке")

            # Таблица красных карточек кубка
            st.markdown('<div class="stat-title">🟥 Красные карточки (Кубок)</div>', unsafe_allow_html=True)
            cup_red = df_cup[df_cup['red_cards'] > 0].sort_values('red_cards', ascending=False)
            if not cup_red.empty:
                st.dataframe(
                    cup_red[['name', 'team', 'red_cards']]
                    .rename(columns={
                        'name': 'Игрок',
                        'team': 'Команда',
                        'red_cards': 'Красные'
                    }),
                    column_config={
                        "Красные": st.column_config.NumberColumn(format="%d")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Нет данных о красных карточках в кубке")

    # Кнопки скачивания (общие для обоих турниров)
    st.markdown("---")
    st.subheader("Экспорт данных")
    col1, col2, col3 = st.columns(3)

    with col1:
        if tournament_type == "Чемпионат":
            data = scorers.to_csv(index=False, encoding='utf-8-sig') if 'scorers' in locals() else ""
            st.download_button(
                label="📥 Голы (CSV)",
                data=data,
                file_name="goals_stats.csv",
                mime="text/csv",
                disabled=not ('scorers' in locals())
            )
        else:
            data = cup_scorers.to_csv(index=False, encoding='utf-8-sig') if 'cup_scorers' in locals() else ""
            st.download_button(
                label="📥 Голы (CSV)",
                data=data,
                file_name="cup_goals_stats.csv",
                mime="text/csv",
                disabled=not ('cup_scorers' in locals())
            )

    with col2:
        if tournament_type == "Чемпионат":
            data = yellow_cards.to_csv(index=False, encoding='utf-8-sig') if 'yellow_cards' in locals() else ""
            st.download_button(
                label="📥 Жёлтые (CSV)",
                data=data,
                file_name="yellow_cards_stats.csv",
                mime="text/csv",
                disabled=not ('yellow_cards' in locals())
            )
        else:
            data = cup_yellow.to_csv(index=False, encoding='utf-8-sig') if 'cup_yellow' in locals() else ""
            st.download_button(
                label="📥 Жёлтые (CSV)",
                data=data,
                file_name="cup_yellow_cards_stats.csv",
                mime="text/csv",
                disabled=not ('cup_yellow' in locals())
            )

    with col3:
        if tournament_type == "Чемпионат":
            data = red_cards.to_csv(index=False, encoding='utf-8-sig') if 'red_cards' in locals() else ""
            st.download_button(
                label="📥 Красные (CSV)",
                data=data,
                file_name="red_cards_stats.csv",
                mime="text/csv",
                disabled=not ('red_cards' in locals())
            )
        else:
            data = cup_red.to_csv(index=False, encoding='utf-8-sig') if 'cup_red' in locals() else ""
            st.download_button(
                label="📥 Красные (CSV)",
                data=data,
                file_name="cup_red_cards_stats.csv",
                mime="text/csv",
                disabled=not ('cup_red' in locals())
            )

    def pluralize_ochko(count):
        if count % 10 == 1 and count % 100 != 11:
            return "очко"
        elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
            return "очка"
        else:
            return "очков"

    with tab5:  # Анонс тура

        try:
            matches = pd.read_csv("matches.csv", encoding='utf-8-sig')
            schedule = pd.read_csv("schedule.csv", encoding='utf-8-sig')
            with open("squads.json", 'r', encoding='utf-8') as f:
                squads = json.load(f)
        except Exception as e:
            st.error(f"Ошибка загрузки данных: {e}")
            st.stop()

        # Очистка и преобразование
        schedule["Дата"] = pd.to_datetime(schedule["Дата"].astype(str) + ".2025", format="%d.%m.%Y", errors="coerce")
        today = pd.to_datetime(datetime.now().date())
        future_schedule = schedule[schedule["Дата"] >= today].sort_values("Дата")

        if future_schedule.empty:
            st.info("Все туры завершены.")
        else:
            next_round = future_schedule.iloc[0]["Тур"]
            st.subheader(f"⚽ Предстоящий тур: №{next_round}" )
            round_matches = schedule[schedule["Тур"] == next_round]

            # Вывод списка матчей
            st.markdown("### 🗓 Матчи тура:")
            for _, match in round_matches.iterrows():
                st.markdown(f"- **{match['Хозяева']} — {match['Гости']}**, {match['Дата'].strftime('%d.%m.%Y')}")

            # Турнирная таблица
            matches["Голы хозяев"] = pd.to_numeric(matches["Голы хозяев"], errors='coerce')
            matches["Голы гостей"] = pd.to_numeric(matches["Голы гостей"], errors='coerce')
            played = matches.dropna(subset=["Голы хозяев", "Голы гостей"])
            teams = pd.unique(matches[["Хозяева", "Гости"]].values.ravel())
            stats = {team: {"Игры": 0, "Победы": 0, "Ничьи": 0, "Поражения": 0,
                            "Забито": 0, "Пропущено": 0, "Очки": 0} for team in teams}

            for _, row in played.iterrows():
                home, away = row["Хозяева"], row["Гости"]
                hg, ag = int(row["Голы хозяев"]), int(row["Голы гостей"])

                stats[home]["Игры"] += 1
                stats[away]["Игры"] += 1
                stats[home]["Забито"] += hg
                stats[home]["Пропущено"] += ag
                stats[away]["Забито"] += ag
                stats[away]["Пропущено"] += hg

                if hg > ag:
                    stats[home]["Победы"] += 1
                    stats[home]["Очки"] += 3
                    stats[away]["Поражения"] += 1
                elif ag > hg:
                    stats[away]["Победы"] += 1
                    stats[away]["Очки"] += 3
                    stats[home]["Поражения"] += 1
                else:
                    stats[home]["Ничьи"] += 1
                    stats[away]["Ничьи"] += 1
                    stats[home]["Очки"] += 1
                    stats[away]["Очки"] += 1

            table_data = [{
                "Команда": t,
                "Очки": s["Очки"],
                "Разница": s["Забито"] - s["Пропущено"]
            } for t, s in stats.items()]
            df_table = pd.DataFrame(table_data)
            leaders = df_table.sort_values(by=["Очки", "Разница"], ascending=False).head(3)

            st.markdown("### 🥇 Лидеры таблицы:")
            for _, row in leaders.iterrows():
                word = pluralize_ochko(row['Очки'])
                st.markdown(f"- {row['Команда']} — {row['Очки']} {word} (разница {row['Разница']})")

            # Бомбардиры
            all_players = []
            for team, players in squads.items():
                for player in players:
                    all_players.append({"Игрок": player["name"], "Голы": player["goals"], "Команда": team})

            df_players = pd.DataFrame(all_players)
            top_scorers = df_players[df_players["Голы"] > 0].sort_values("Голы", ascending=False).head(3)

            st.markdown("### 🎯 Лучшие бомбардиры:")
            for _, row in top_scorers.iterrows():
                st.markdown(f"- {row['Игрок']} ({row['Команда']}) — {row['Голы']} гол(ов)")

            # st.markdown("### 🟥 Дисквалификации:")
            # st.markdown(f"- {""} ({"ФК Параты"}) - {"удаление"}")