import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Футбол Волжского района 2025", layout="wide")

# Боковое меню для выбора страницы
page = st.sidebar.selectbox("Выберите раздел", ["Чемпионат", "Кубок", "Составы команд", "Статистика"])

if page == "Чемпионат":
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("volzhsky_flag.jpg", use_container_width=True)
    with col2:
        st.title("🏆 Чемпионат Волжского района по футболу 2025 года")

    matches = pd.read_csv("matches.csv")
    df_schedule = pd.read_csv("schedule.csv")

    teams = pd.unique(matches[["Хозяева", "Гости"]].values.ravel())
    stats = {team: {"Игры": 0, "Победы": 0, "Ничьи": 0, "Поражения": 0, "Забито": 0, "Пропущено": 0, "Очки": 0} for team in teams}

    for _, row in matches.iterrows():
        home, away = row["Хозяева"], row["Гости"]
        hg, ag = row["Голы хозяев"], row["Голы гостей"]
        if hg == 0 and ag == 0 and row["Тур"] != 1:
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
        s["Разница мячей"] = s["Забито"] - s["Пропущено"]
        table_data.append({"Команда": team, **s})

    df = pd.DataFrame(table_data)
    df = df.sort_values(by=["Очки", "Разница мячей"], ascending=[False, False]).reset_index(drop=True)
    df.insert(0, "№", range(1, len(df) + 1))
    cols = df.columns.tolist()
    cols.remove("Очки")
    cols.append("Очки")
    df = df[cols]

    st.subheader("📊 Турнирная таблица")
    st.dataframe(df, use_container_width=True)

    st.subheader("🎯 Результаты матчей")
    played_rounds = matches[(matches["Голы хозяев"] > 0) | (matches["Голы гостей"] > 0)]["Тур"].unique()
    played_rounds = sorted(played_rounds)
    if played_rounds:
        selected_round = st.selectbox("Выберите тур", played_rounds)
        match_filter = matches[matches["Тур"] == selected_round]
        st.dataframe(match_filter[["Хозяева", "Гости", "Голы хозяев", "Голы гостей"]], use_container_width=True)
    else:
        st.info("Пока нет сыгранных туров.")

    st.subheader("🗓 Расписание матчей (по турам)")
    df_schedule["Дата"] = pd.to_datetime(df_schedule["Дата"].astype(str) + ".2025", format="%d.%m.%Y", errors="coerce")
    df_schedule["Дата"] = df_schedule["Дата"].dt.strftime("%d.%m.%Y")
    today = pd.to_datetime(datetime.now().date())
    future_rounds = pd.to_datetime(df_schedule["Дата"], format="%d.%m.%Y", errors="coerce")
    default_round = df_schedule.loc[future_rounds >= today, "Тур"].min() if not future_rounds.empty else df_schedule["Тур"].max()
    selected_schedule_round = st.selectbox(
        "Выберите тур для просмотра расписания",
        sorted(df_schedule["Тур"].unique()),
        index=list(sorted(df_schedule["Тур"].unique())).index(default_round),
        key="schedule"
    )
    st.dataframe(df_schedule[df_schedule["Тур"] == selected_schedule_round], use_container_width=True)

elif page == "Кубок":
    st.title("🏆 Кубок Волжского района по футболу 2025 года")

    # CSS стили для таблицы
    st.markdown("""
    <style>
    .cup-table {
        width: 100%;
        border-collapse: collapse;
    }
    .cup-table th {
        background-color: #4CAF50;
        color: white;
        padding: 10px;
        text-align: center;
    }
    .cup-table td {
        padding: 8px;
        border-bottom: 1px solid #ddd;
        text-align: center;
    }
    .cup-table tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .winner {
        font-weight: bold;
        color: #2e7d32;
    }
    .stage-header {
        font-size: 1.2em;
        color: #2c3e50;
        margin: 20px 0 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Данные матчей кубка (пример)
    cup_matches = [
        # 1/8 финала
        {"stage": "1/8 финала", "date": "07.05.2025", "home": "ФК Эмеково", "away": "ФК Приволжск", "score": "3:0"},
        {"stage": "1/8 финала", "date": "21.05.2025", "home": "ФК Приволжск", "away": "ФК Эмеково", "score": None},

        # 1/4 финала
        {"stage": "1/4 финала", "date": "04.06.2025", "home": "ФК Помары", "away": "ФК Сотнур", "score": None},
        {"stage": "1/4 финала", "date": "18.06.2025", "home": "ФК Сотнур", "away": "ФК Помары", "score": None},
        {"stage": "1/4 финала", "date": "04.06.2025", "home": "ФК Параты", "away": "ФК Часовенная", "score": None},
        {"stage": "1/4 финала", "date": "18.06.2025", "home": "ФК Часовенная", "away": "ФК Параты", "score": None},
        {"stage": "1/4 финала", "date": "04.06.2025", "home": "Поб. Эмеково/Приволжск", "away": "ФК Ярамор",
         "score": None},
        {"stage": "1/4 финала", "date": "18.06.2025", "home": "ФК Ярамор", "away": "Поб. Эмеково/Приволжск",
         "score": None},
        {"stage": "1/4 финала", "date": "04.06.2025", "home": "ФК Петъял", "away": "ФК Карамассы", "score": None},
        {"stage": "1/4 финала", "date": "18.06.2025", "home": "ФК Карамассы", "away": "ФК Петъял", "score": None},

        # 1/2 финала
        {"stage": "1/2 финала", "date": "02.07.2025", "home": "?", "away": "?", "score": None},
        {"stage": "1/2 финала", "date": "16.07.2025", "home": "?", "away": "?", "score": None},

        # Финал
        {"stage": "Финал", "date": "30.07.2025", "home": "?", "away": "?", "score": None}
    ]

    # Группировка по этапам
    stages = {
        "1/8 финала": [],
        "1/4 финала": [],
        "1/2 финала": [],
        "Финал": []
    }

    for match in cup_matches:
        stages[match["stage"]].append(match)

    # Отображение таблиц для каждого этапа
    for stage, matches in stages.items():
        st.markdown(f'<div class="stage-header">{stage}</div>', unsafe_allow_html=True)

        # Создаем DataFrame для таблицы
        df = pd.DataFrame(matches)


        # Форматирование счёта и выделение победителя
        def format_match(row):
            if pd.isna(row["score"]):
                return f"{row['home']} - {row['away']}"

            home_goals, away_goals = map(int, row["score"].split(':'))

            home = f"<span class='winner'>{row['home']}</span>" if home_goals > away_goals else row['home']
            away = f"<span class='winner'>{row['away']}</span>" if away_goals > home_goals else row['away']

            return f"{home} - {away} <b>({row['score']})</b>"


        df["Матч"] = df.apply(format_match, axis=1)

        # Отображаем таблицу
        st.markdown(
            df[["date", "Матч"]]
            .rename(columns={"date": "Дата"})
            .to_html(escape=False, index=False, classes="cup-table"),
            unsafe_allow_html=True
        )

elif page == "Составы команд":
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

        # Добавляем колонку с фото (заглушки)
        df['Фото'] = "👤"

        # Отображаем таблицу с отдельными столбцами для карточек
        st.dataframe(
            df[['Фото', 'name', 'number', 'position', 'goals', 'assists', 'yellow_cards', 'red_cards']]
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
                "Фото": st.column_config.TextColumn("Фото"),
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

elif page == "Статистика":
    st.title("📊 Статистика игроков")

    # Загрузка данных
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
        st.markdown('<div class="stat-title">🏅 Лучшие бомбардиры</div>', unsafe_allow_html=True)
        scorers = df[df['goals'] > 0].sort_values('goals', ascending=False)
        if not scorers.empty:
            st.dataframe(
                scorers[['team', 'name', 'position', 'goals']]
                .rename(columns={
                    'team': 'Команда',
                    'name': 'Игрок',
                    'position': 'Позиция',
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
        st.markdown('<div class="stat-title">🟨 Нарушители (желтые карточки)</div>', unsafe_allow_html=True)
        yellow_cards = df[df['yellow_cards'] > 0].sort_values('yellow_cards', ascending=False)
        if not yellow_cards.empty:
            st.dataframe(
                yellow_cards[['team', 'name', 'position', 'yellow_cards']]
                .rename(columns={
                    'team': 'Команда',
                    'name': 'Игрок',
                    'position': 'Позиция',
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
        st.markdown('<div class="stat-title">🟥 Агрессивные нарушения (красные карточки)</div>', unsafe_allow_html=True)
        red_cards = df[df['red_cards'] > 0].sort_values('red_cards', ascending=False)
        if not red_cards.empty:
            st.dataframe(
                red_cards[['team', 'name', 'position', 'red_cards']]
                .rename(columns={
                    'team': 'Команда',
                    'name': 'Игрок',
                    'position': 'Позиция',
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

        # Кнопки скачивания
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📥 Голы (CSV)",
                data=scorers.to_csv(index=False, encoding='utf-8-sig'),
                file_name="goals_stats.csv",
                mime="text/csv"
            )
        with col2:
            st.download_button(
                label="📥 Жёлтые (CSV)",
                data=yellow_cards.to_csv(index=False, encoding='utf-8-sig'),
                file_name="yellow_cards_stats.csv",
                mime="text/csv"
            )
        with col3:
            st.download_button(
                label="📥 Красные (CSV)",
                data=red_cards.to_csv(index=False, encoding='utf-8-sig'),
                file_name="red_cards_stats.csv",
                mime="text/csv"
            )
