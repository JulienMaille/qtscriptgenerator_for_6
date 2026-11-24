#ifndef ENUMEXPRESSION_H
#define ENUMEXPRESSION_H

#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <functional>
#include <limits>
#include <string>

class EnumExpression
{
public:
    using Resolver = std::function<bool(const std::string &, int &)>;

    static bool evaluate(const std::string &text, const Resolver &resolver, int &result)
    {
        EnumExpression parser(text, resolver);
        uint32_t value = parser.expression(0);
        parser.space();
        if (!parser.valid || parser.position != text.size())
            return false;
        result = value <= uint32_t(std::numeric_limits<int32_t>::max())
            ? int(value) : -1 - int(~value);
        return true;
    }

private:
    EnumExpression(const std::string &text, const Resolver &resolver)
        : text(text),
          resolver(resolver) {}

    void space()
    {
        while (position < text.size() && (text[position] == ' ' || text[position] == '\t'
               || text[position] == '\r' || text[position] == '\n'))
            ++position;
    }

    bool take(const std::string &token)
    {
        space();
        if (text.compare(position, token.size(), token) == 0) {
            position += token.size();
            return true;
        }
        return false;
    }

    int binaryPrecedence()
    {
        char c = text[position];
        switch (c) {
        case '|': return 1;
        case '^': return 2;
        case '&': return 3;
        case '<': case '>':
            return position + 1 < text.size() && text[position + 1] == c ? 4 : 0;
        case '+': case '-': return 5;
        case '*': case '/': case '%': return 6;
        }
        return -1;
    }

    uint32_t expression(int minPrecedence)
    {
        uint32_t left = unary();
        while (valid) {
            space();
            if (position >= text.size())
                break;
            int precedence = binaryPrecedence();
            if (precedence < minPrecedence)
                break;
            char op = text[position];
            position += unsigned(op == '<' || op == '>') + 1;
            uint32_t right = expression(precedence + 1);
            left = apply(left, op, right);
        }
        return left;
    }

    uint32_t unary()
    {
        space();
        if (take("(")) {
            uint32_t value = expression(0);
            if (!take(")"))
                valid = false;
            return value;
        }
        if (take("~"))
            return ~unary();
        if (take("-"))
            return uint32_t(-int(unary()));
        if (take("+"))
            return unary();
        return primary();
    }

    uint32_t primary()
    {
        space();
        bool hex = position + 1 < text.size() && text[position] == '0'
            && (text[position + 1] == 'x' || text[position + 1] == 'X');
        if (hex || (position < text.size() && isdigit(text[position]))) {
            position += hex ? 2 : 0;
            size_t digitStart = position;
            while (position < text.size() && (hex ? isxdigit(text[position]) != 0
                                                  : isdigit(text[position]) != 0))
                ++position;
            if (position == digitStart) {
                valid = false;
                return 0;
            }
            uint32_t value = uint32_t(strtoull(text.substr(digitStart, position - digitStart).c_str(),
                                               0, hex ? 16 : 10));
            if (position < text.size() && (text[position] == 'u' || text[position] == 'U'
                || text[position] == 'l' || text[position] == 'L'))
                ++position;
            space();
            if (position < text.size() && (isalnum(text[position]) || text[position] == '_'))
                valid = false;
            return value;
        }
        if (position < text.size() && (isalpha(text[position]) || text[position] == '_'
            || text[position] == ':')) {
            size_t start = position;
            while (position < text.size() && (isalnum(text[position]) || text[position] == '_'
                   || text[position] == ':'))
                ++position;
            int value = 0;
            if (!resolver(text.substr(start, position - start), value)) {
                valid = false;
                return 0;
            }
            return uint32_t(value);
        }
        valid = false;
        return 0;
    }

    static uint32_t apply(uint32_t left, char op, uint32_t right)
    {
        switch (op) {
        case '|': return uint32_t(int(left) | int(right));
        case '^': return uint32_t(int(left) ^ int(right));
        case '&': return uint32_t(int(left) & int(right));
        case '<': return left << uint32_t(right & 31);
        case '>': return left >> uint32_t(right & 31);
        case '+': return uint32_t(int(left) + int(right));
        case '-': return uint32_t(int(left) - int(right));
        case '*': return uint32_t(int(left) * int(right));
        case '/': return right == 0 ? 0 : uint32_t(int(left) / int(right));
        case '%': return right == 0 ? 0 : uint32_t(int(left) % int(right));
        }
        return 0;
    }

    const std::string &text;
    const Resolver &resolver;
    size_t position = 0;
    bool valid = true;
};

#endif
