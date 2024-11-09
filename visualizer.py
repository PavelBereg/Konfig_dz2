import csv
import subprocess
import sys
import os
import argparse
from datetime import datetime

def parse_config(config_path):
    """Парсинг CSV-конфигурации."""
    with open(config_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        config = next(reader)
        graphviz_path, repo_path, output_path, date_str = config
        graphviz_path = graphviz_path.strip('"')
        repo_path = repo_path.strip('"')
        output_path = output_path.strip('"')
        date = datetime.strptime(date_str.strip(), '%Y-%m-%d')
        return graphviz_path, repo_path, output_path, date

def get_commits(repo_path, date):
    """Получение списка коммитов с информацией позже указанной даты."""
    cmd = f'git -C "{repo_path}" log --pretty=format:%H --since="{date.strftime("%Y-%m-%d")}"'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', shell=True)
    if result.returncode != 0:
        print(f"Ошибка при выполнении команды git: {result.stderr}")
        sys.exit(1)
    commits = result.stdout.strip().split('\n')
    commits.reverse()
    return commits

def get_commit_info(repo_path, commit_hash):
    """Получение информации о коммите: сообщение и измененные файлы."""
    # Получение сообщения коммита
    message_cmd = f'git -C "{repo_path}" log -1 --pretty=format:%s {commit_hash}'
    message_result = subprocess.run(message_cmd, stdout=subprocess.PIPE, text=True, encoding='utf-8', shell=True)
    message = message_result.stdout.strip()

    # Получение списка измененных файлов
    files_cmd = f'git -C "{repo_path}" diff-tree --no-commit-id --name-only -r {commit_hash}'
    files_result = subprocess.run(files_cmd, stdout=subprocess.PIPE, text=True, encoding='utf-8', shell=True)
    files = files_result.stdout.strip().split('\n') if files_result.stdout.strip() else []

    print(f"Коммит {commit_hash}: файлы - {files}")  # Отладочный вывод для проверки

    return message, files




def get_commit_parents(repo_path, commit_hash):
    """Получение списка родительских коммитов."""
    cmd = f'git -C "{repo_path}" rev-list --parents -n 1 {commit_hash}'
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', shell=True)
    if result.returncode != 0:
        print(f"Ошибка при выполнении команды git: {result.stderr}")
        sys.exit(1)
    parts = result.stdout.strip().split()
    return parts[1:] if len(parts) > 1 else []

def build_dependency_graph(repo_path, commits):
    """Построение графа зависимостей с дополнительной информацией о коммитах."""
    graph = {}
    for commit in commits:
        parents = get_commit_parents(repo_path, commit)
        message, files = get_commit_info(repo_path, commit)
        graph[commit] = {'parents': parents, 'message': message, 'files': files}
    return graph


def generate_mermaid_code(graph):
    """Генерация кода Mermaid для графа зависимостей с подробной информацией."""
    lines = ["graph TD"]
    for commit, data in graph.items():
        # Формируем информацию для коммита
        commit_label = f'Commit: {commit[:7]}<br>Message: {data["message"] if data["message"] else "No message"}'

        # Обработка файлов
        if data['files']:
            files_str = ', '.join(data['files'])
            commit_label += f'<br>Files: {files_str}'
        else:
            commit_label += '<br>Files:'

        lines.append(f'    {commit[:7]}["{commit_label}"]')

        # Добавляем зависимости
        for parent in data['parents']:
            lines.append(f'    {parent[:7]} --> {commit[:7]}')

    return '\n'.join(lines)



def output_result(mermaid_code, output_path):
    """Сохранение кода Mermaid в формате Markdown в файл."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("```mermaid\n")
        f.write(mermaid_code)
        f.write("\n```")
    print("Код Mermaid сохранен в файл.")

def generate_image(visualizer_path, input_path, output_path):
    try:
        result = subprocess.run(
            [visualizer_path, "-i", input_path, "-o", output_path],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            with open("error_log.txt", "w", encoding="utf-8") as error_file:
                error_file.write(result.stderr)
            print(f"Ошибка при генерации изображения: {result.stderr}")
        else:
            print(f"Изображение графа успешно сгенерировано: {output_path}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

def main():
    parser = argparse.ArgumentParser(description="Визуализация графа зависимостей git-репозитория")
    parser.add_argument("visualizer_path", type=str, help="Путь к программе для визуализации графов")
    parser.add_argument("repo_path", type=str, help="Путь к анализируемому репозиторию")
    parser.add_argument("output_path", type=str, help="Путь к файлу с изображением графа зависимостей")
    parser.add_argument("date", type=str, help="Дата в формате YYYY-MM-DD")
    args = parser.parse_args()

    date = datetime.strptime(args.date, '%Y-%m-%d')

    commits = get_commits(args.repo_path, date)
    graph = build_dependency_graph(args.repo_path, commits)
    mermaid_code = generate_mermaid_code(graph)

    output_result(mermaid_code, args.output_path)
    output_image_path = os.path.splitext(args.output_path)[0] + '.png'
    generate_image(args.visualizer_path, args.output_path, output_image_path)

if __name__ == '__main__':
    main()
