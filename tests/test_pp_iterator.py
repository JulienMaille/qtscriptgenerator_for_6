#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = r'''
#include <string>
#include "parser/rpp/pp-iterator.h"
int main() {
    std::string left, right = "abc";
    rpp::pp_output_iterator<std::string> a(left), b(right);
    *a++ = 'x';
    a = b;
    *a++ = 'y';
    return left == "abcy" && right == "abc" ? 0 : 1;
}
'''
with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    (temp / 'probe.cpp').write_text(source)
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++17', '-Werror',
                    '-Wno-deprecated-declarations', '-I' + str(root / 'generator'),
                    str(temp / 'probe.cpp'), '-o', str(temp / 'probe')], check=True)
    subprocess.run([str(temp / 'probe')], check=True)
print('Preprocessor iterator regression checks passed')