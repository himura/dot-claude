#!/usr/bin/env python3
"""
TypeScript + React の悪いお作法を検出するスクリプト
Claude Code hooks で使用される
"""

import json
import re
import sys
from typing import List, Dict, Any


class ReactCodeChecker:
    """React/TypeScript コード品質チェッカー"""

    def __init__(self):
        self.patterns = {
            'useEffect_data_transform': {
                'pattern': r'useEffect\s*\([^}]*\.(map|filter|reduce|join)\s*\(',
                'message': "\n".join([
                    'useEffect内でのデータ変換を検出しました。レンダー中に直接計算することを検討してください。',
                    'useEffect は Escape hatch であり、乱用は避けるべきです。下記のドキュメントを参照してください。',
                    'https://react.dev/learn/you-might-not-need-an-effect'
                ]),
                'severity': 'high'
            },
            'useEffect_state_sync': {
                'pattern': r'useEffect\s*\([^}]*set[A-Z][a-zA-Z]*\s*\(',
                'message': "\n".join([
                    'useEffect内での状態更新を検出しました。デバッグが困難なバグの原因になる可能性が高いです。このような更新操作が必要な場合は、大抵の場合で、設計の見直しが必要です。',
                    'useEffect は Escape hatch であり、乱用は避けるべきです。下記のドキュメントを参照してください。',
                    'https://react.dev/learn/you-might-not-need-an-effect',
                ]),
                'severity': 'high'
            },
            'any_type': {
                'pattern': r':\s*any\b|<any>|\bany\s|\bany\[',
                'message': 'any型の使用を検出しました。具体的な型定義を検討してください。',
                'severity': 'high'
            },
            'inline_functions': {
                'pattern': r'onClick=\{[^}]*=>',
                'message': 'onClick内でのインライン関数定義を検出しました。useCallbackまたは外部での関数定義を検討してください。',
                'severity': 'medium'
            },
            'direct_dom': {
                'pattern': r'document\.(getElementById|querySelector|createElement)',
                'message': '直接のDOM操作を検出しました。Reactのrefまたは宣言的なアプローチを検討してください。',
                'severity': 'high'
            },
            'console_logs': {
                'pattern': r'console\.(log|debug|info)',
                'message': 'console.log等のデバッグコードを検出しました。本番コードから削除することを検討してください。',
                'severity': 'low'
            },
            'props_drilling': {
                'pattern': r'props\.[a-zA-Z]+\.[a-zA-Z]+\.',
                'message': '深いprops参照を検出しました。Context APIまたは状態管理ライブラリの使用を検討してください。',
                'severity': 'medium'
            },
            'promise_chains': {
                'pattern': r'\.then\s*\([^)]*\)\s*\.catch\s*\(',
                'message': 'Promise chainを検出しました。async/awaitの使用を検討してください。',
                'severity': 'low'
            }
        }

    def check_multiple_useEffect(self, content: str) -> List[str]:
        """複数のuseEffect使用をチェック"""
        violations = []
        empty_deps_count = len(re.findall(r'useEffect\s*\([^}]*\[\s*\]', content))
        if empty_deps_count > 2:
            violations.append(
                f'複数の useEffect(..., []) を検出しました（{empty_deps_count}個）。'
                'コンポーネントの責任が大きすぎる可能性があります。'
            )
        return violations

    def check_complex_jsx(self, content: str) -> List[str]:
        """複雑なJSX構造をチェック"""
        violations = []
        jsx_tag_count = len(re.findall(r'<[^/!]', content))
        if jsx_tag_count > 20:
            violations.append(
                f'複雑なJSX構造を検出しました（{jsx_tag_count}個のタグ）。'
                'コンポーネントの分割を検討してください。'
            )
        return violations

    def check_code(self, content: str) -> List[Dict[str, str]]:
        """コードをチェックして違反を返す"""
        violations = []

        # パターンベースのチェック
        for rule_name, rule_config in self.patterns.items():
            if re.search(rule_config['pattern'], content, re.DOTALL):
                violations.append({
                    'rule': rule_name,
                    'message': rule_config['message'],
                    'severity': rule_config['severity']
                })

        # 特別なチェック
        for violation in self.check_multiple_useEffect(content):
            violations.append({
                'rule': 'multiple_useEffect',
                'message': violation,
                'severity': 'medium'
            })

        for violation in self.check_complex_jsx(content):
            violations.append({
                'rule': 'complex_jsx',
                'message': violation,
                'severity': 'medium'
            })

        return violations


def is_react_typescript_file(file_path: str, content: str) -> bool:
    """React/TypeScriptファイルかどうかを判定"""
    if file_path and re.search(r'\.(tsx?|jsx?)$', file_path):
        return True
    if re.search(r'(import.*react|from [\'"]react)', content):
        return True
    return False


def main():
    """メイン処理"""
    try:
        # stdinからJSONデータを読み取り
        input_data = json.loads(sys.stdin.read())

        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})

        file_path = tool_input.get('file_path', '')
        new_string = tool_input.get('new_string') or tool_input.get('content', '')

        # Edit/Write/MultiEditツールのみ対象
        if tool_name not in ['Edit', 'Write', 'MultiEdit']:
            sys.exit(0)

        # React/TypeScriptファイルかチェック
        if not is_react_typescript_file(file_path, new_string):
            sys.exit(0)

        # コード品質チェック実行
        checker = ReactCodeChecker()
        violations = checker.check_code(new_string)

        if violations:
            # エラー出力
            print("🔍 React/TypeScript コード品質チェック", file=sys.stderr)
            print("━" * 60, file=sys.stderr)
            print(f"ツール: {tool_name}", file=sys.stderr)
            print(f"ファイル: {file_path}", file=sys.stderr)
            print("", file=sys.stderr)
            print("⚠️  検出された問題:", file=sys.stderr)

            for violation in violations:
                severity_icon = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(violation['severity'], '⚪')
                print(f"   {severity_icon} {violation['message']}", file=sys.stderr)

            print("", file=sys.stderr)
            print("💡 これらの問題は以下の影響を与える可能性があります:", file=sys.stderr)
            print("   - パフォーマンスの低下", file=sys.stderr)
            print("   - 可読性の低下", file=sys.stderr)
            print("   - バグの発生リスク", file=sys.stderr)
            print("   - メンテナンス性の低下", file=sys.stderr)
            print("", file=sys.stderr)
            print("━" * 60, file=sys.stderr)
            print("", file=sys.stderr)
            print("🛑 コード品質の問題により操作をブロックしました", file=sys.stderr)
            print("   修正後に再度お試しください", file=sys.stderr)

            # ツール実行をブロック
            sys.exit(2)

        # 問題なしの場合は続行
        sys.exit(0)

    except Exception as e:
        print(f"チェッカーエラー: {e}", file=sys.stderr)
        # エラー時は続行
        sys.exit(0)


if __name__ == '__main__':
    main()
