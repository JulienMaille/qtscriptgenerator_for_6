#!/usr/bin/env python3
"""Exercise the actual return-expression helper without a Qt installation.

Requires Python 3 and a C++17 compiler (CXX, default: g++). This is a focused
unit test, not a substitute for running the full generator against Qt headers.
"""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'generator/shellimplgenerator.cpp').read_text()
start = source.index('static QString defaultReturnValueText(')
end = source.index('\nstatic void writeOutArgUnpack', start)
helper = source[start:end]
cxx = os.environ.get('CXX', 'g++')
shim = r'''
#include <iostream>
#include <string>
using QLatin1String = std::string;
using QLatin1Char = char;
class QString : public std::string {
public:
    using std::string::string;
    QString(std::string s) : std::string(s) {}
    bool startsWith(const std::string &s) const { return rfind(s, 0) == 0; }
    bool endsWith(char c) const { return !empty() && back() == c; }
    void remove(size_t p, size_t n) { erase(p, n); }
    void chop(size_t n) { erase(size() - n); }
};
struct AbstractMetaType {
    const char *signature; bool reference; bool constant; int pointers;
    bool isReference() const { return reference; }
    bool isConstant() const { return constant; }
    int indirections() const { return pointers; }
    QString cppSignature() const { return signature; }
};
'''
main = r'''
int main() {
    AbstractMetaType cases[] = {
        {"QSize &", true, false, 0}, {"int &", true, false, 0},
        {"QSize *&", true, false, 1}, {"const QSize *&", true, true, 1},
        {"QSize", false, false, 0}, {"QSize *", false, false, 1},
        {"const QSize &", true, true, 0}
    };
    for (auto &t : cases) std::cout << defaultReturnValueText(&t) << '\n';
}
'''
with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    (temp / 'helper.cpp').write_text(shim + helper + main)
    subprocess.run([cxx, '-std=c++17', '-Wall', '-Wextra', '-Werror', str(temp / 'helper.cpp'), '-o', str(temp / 'helper')], check=True)
    expressions = subprocess.check_output([str(temp / 'helper')], text=True).splitlines()
    assert expressions == ['*static_cast<QSize  *>(nullptr)', '*static_cast<int  *>(nullptr)',
                           '*static_cast<QSize * *>(nullptr)', '*static_cast<const QSize * *>(nullptr)',
                           'QSize()', 'nullptr', 'QSize()'], expressions
    types = ['QSize &', 'int &', 'QSize *&', 'const QSize *&', 'QSize', 'QSize *', 'const QSize &']
    # The MSVC-only Qt macro drops its argument. Other compilers see a return.
    for name, macro in [('return', '#define Q_UNREACHABLE_RETURN(...) do { __builtin_unreachable(); return __VA_ARGS__; } while (0)'),
                        ('discard', '#define Q_UNREACHABLE_RETURN(...) __builtin_unreachable()')]:
        functions = '\n'.join(f'{t} f{i}() {{ fatal(); Q_UNREACHABLE_RETURN({e}); }}' for i, (t, e) in enumerate(zip(types, expressions)))
        (temp / 'generated.cpp').write_text('#include <cstdlib>\nstruct QSize {};\n[[noreturn]] void fatal() { std::abort(); }\n' + macro + '\n' + functions)
        # const QSize & retains the existing temporary-return behavior, which
        # compilers may warn about even though the statement is unreachable.
        subprocess.run([cxx, '-std=c++17', '-Werror', '-Wno-error=return-local-addr', '-c', str(temp / 'generated.cpp'), '-o', str(temp / (name + '.o'))], check=True)
    (temp / 'old.cpp').write_text('struct QSize {}; QSize &f() { return QSize(); }\n')
    assert subprocess.run([cxx, '-std=c++17', '-fsyntax-only', str(temp / 'old.cpp')], capture_output=True).returncode != 0
print('Return-expression regression checks passed')
