#include "option.hpp"

#include <gtest/gtest.h>
#include <gmock/gmock.h>

using namespace testing;

TEST(option_tests, should_be_default_constructible)
{
    option op;
}

TEST(option_tests, some_values_should_be_assignable)
{
    option op;

    // note the reassignment, this should be leak-free
    op = 1;
    auto & ref = (op = "hello");

    EXPECT_EQ(&op, &ref);
}

template<class arg_type>
struct case_mock
{
    MOCK_METHOD1_T(call, void(arg_type));

    void operator()(arg_type value)
    {
        call(value);
    }
};

template<class T> using case_strict_mock = StrictMock<case_mock<T>>;

TEST(option_tests, single_value_should_be_matched)
{
    option op;

    op = 1;

    case_strict_mock<int> int_case;
    case_strict_mock<float> float_case;
    case_strict_mock<std::string> string_case;

    EXPECT_CALL(int_case, call(1));
    op.match(
        [&] (int i) { int_case.call(i); },
        [&] (float f) { float_case.call(f); },
        [&] (std::string f) { string_case.call(f); }
    );

    EXPECT_CALL(int_case, call(1));
    op.match(
        [&] (float f) { float_case.call(f); },
        [&] (int i) { int_case.call(i); },
        [&] (std::string f) { string_case.call(f); }
    );

    EXPECT_CALL(int_case, call(1));
    op.match(
        [&] (float f) { float_case.call(f); },
        [&] (std::string f) { string_case.call(f); },
        [&] (int i) { int_case.call(i); }
    );
}
