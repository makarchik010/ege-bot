import os

os.makedirs("lessons_data", exist_ok=True)

for i in range(1, 28):
    file_path = f"lessons_data/lesson_{i}.md"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Задание №{i}\n\n")
            f.write("**Статус:** Материал находится в разработке ⏳\n\n")
            f.write("---\n\n### Теория и шаблон кода\n\nСкоро здесь появится авторский разбор актуальных прототипов.")
