import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
import subprocess
import os
from io import StringIO

# Импортируем функции из вашего кода
from visualizer import (
    parse_config,
    get_commits,
    get_commit_info,
    get_commit_parents,
    build_dependency_graph,
    generate_mermaid_code,
    output_result,
    generate_image
)

class TestGitVisualizer(unittest.TestCase):

    def test_parse_config(self):
        # Тестирование функции parse_config
        test_csv_content = '"C:\\Program Files\\Graphviz\\bin\\dot.exe","C:\\path\\to\\repo","C:\\path\\to\\output.md","2023-10-01"\n'
        with patch('builtins.open', mock_open(read_data=test_csv_content)):
            graphviz_path, repo_path, output_path, date = parse_config('config.csv')
            self.assertEqual(graphviz_path, 'C:\\Program Files\\Graphviz\\bin\\dot.exe')
            self.assertEqual(repo_path, 'C:\\path\\to\\repo')
            self.assertEqual(output_path, 'C:\\path\\to\\output.md')
            self.assertEqual(date, datetime(2023, 10, 1))

    @patch('subprocess.run')
    def test_get_commits(self, mock_run):
        # Тестирование функции get_commits
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='commit_hash_1\ncommit_hash_2\n', stderr=''
        )
        date = datetime(2023, 10, 1)
        commits = get_commits('C:\\path\\to\\repo', date)
        self.assertEqual(commits, ['commit_hash_2', 'commit_hash_1'])  # Проверяем, что список перевернут

    @patch('subprocess.run')
    def test_get_commit_info(self, mock_run):
        # Тестирование функции get_commit_info
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout='Initial commit\n', stderr=''),
            subprocess.CompletedProcess(args=[], returncode=0, stdout='file1.py\nfile2.py\n', stderr='')
        ]
        message, files = get_commit_info('C:\\path\\to\\repo', 'commit_hash_1')
        self.assertEqual(message, 'Initial commit')
        self.assertEqual(files, ['file1.py', 'file2.py'])

    @patch('subprocess.run')
    def test_get_commit_parents(self, mock_run):
        # Тестирование функции get_commit_parents
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='commit_hash_1 parent_hash_1 parent_hash_2\n', stderr=''
        )
        parents = get_commit_parents('C:\\path\\to\\repo', 'commit_hash_1')
        self.assertEqual(parents, ['parent_hash_1', 'parent_hash_2'])

    def test_build_dependency_graph(self):
        # Тестирование функции build_dependency_graph
        commits = ['commit_hash_1', 'commit_hash_2']
        with patch('visualizer.get_commit_info') as mock_get_info, \
             patch('visualizer.get_commit_parents') as mock_get_parents:

            mock_get_info.side_effect = [('Initial commit', ['file1.py']), ('Added new features', ['file2.py', 'file3.py'])]
            mock_get_parents.side_effect = [['parent_hash_1'], ['commit_hash_1']]

            graph = build_dependency_graph('C:\\path\\to\\repo', commits)

            expected_graph = {
                'commit_hash_1': {
                    'message': 'Initial commit',
                    'files': ['file1.py'],
                    'parents': ['parent_hash_1']
                },
                'commit_hash_2': {
                    'message': 'Added new features',
                    'files': ['file2.py', 'file3.py'],
                    'parents': ['commit_hash_1']
                }
            }

            self.assertEqual(graph, expected_graph)

    def test_generate_mermaid_code(self):
        # Создайте пример графа с коммитами
        graph = {
            'commit_hash_1': {
                'parents': [],
                'message': 'Initial commit',
                'files': ['file1.py']
            },
            'commit_hash_2': {
                'parents': ['commit_hash_1'],
                'message': 'Added new features',
                'files': ['file2.py', 'file3.py']
            }
        }

        expected_code = """
        graph TD
            commit_hash_1["Commit: commit_hash_1<br>Message: Initial commit<br>Files: file1.py"]
            commit_hash_1 --> commit_hash_2
            commit_hash_2["Commit: commit_hash_2<br>Message: Added new features<br>Files: file2.py, file3.py"]
        """

        # Генерация кода Mermaid
        mermaid_code = generate_mermaid_code(graph)

        # Проверка, что сгенерированный код соответствует ожидаемому
        self.assertEqual(mermaid_code.strip(), expected_code.strip())

        mermaid_code = generate_mermaid_code(graph)
        self.assertEqual(mermaid_code.strip(), expected_code.strip())

    @patch('builtins.open', new_callable=mock_open)
    def test_output_result(self, mock_file):
        # Тестирование функции output_result
        mermaid_code = 'graph TD\n    ...'
        output_result(mermaid_code, 'C:\\path\\to\\output.md')

        # Проверяем, что файл был открыт для записи
        mock_file.assert_called_once_with('C:\\path\\to\\output.md', 'w', encoding='utf-8')
        # Проверяем, что данные были записаны в файл
        mock_file().write.assert_any_call("```mermaid\n")
        mock_file().write.assert_any_call(mermaid_code)
        mock_file().write.assert_any_call("\n```")

    @patch('subprocess.run')
    def test_generate_image(self, mock_run):
        # Тестирование функции generate_image
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        generate_image('C:\\Program Files\\Graphviz\\bin\\dot.exe', 'input.md', 'output.png')
        mock_run.assert_called_once_with(['C:\\Program Files\\Graphviz\\bin\\dot.exe', '-i', 'input.md', '-o', 'output.png'],
                                         capture_output=True, text=True)

if __name__ == '__main__':
    unittest.main()
