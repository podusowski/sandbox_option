#include "option.hpp"

#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include <memory>

using namespace testing;

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

TEST(option_tests, should_be_default_constructible)
{
    option op;
}

TEST(option_tests, some_values_should_be_assignable)
{
    option op;

    // note the reassignment, this should be leak-free
    op = 1;
    auto & ref = (op = std::string("hello"));

    EXPECT_EQ(&op, &ref);
}

TEST(option_tests, convert_constructor_can_be_used_for_assignment)
{
    option op{1};

    case_strict_mock<int> int_case;

    EXPECT_CALL(int_case, call(1));
    op.match([&] (int i) { int_case.call(i); });
}

TEST(option_tests, movable_only_types_should_be_supported)
{
    option op;

    op = std::make_unique<int>(1);
}

TEST(option_tests, reference_types_should_be_supported)
{
    option op;

    int i = 5;
    int & ref = i;

    op = ref;

    case_strict_mock<int> int_case;

    EXPECT_CALL(int_case, call(5));
    op.match([&] (int i) { int_case.call(i); });
}

TEST(option_tests, const_references_in_case_should_match_the_type)
{
    option op = 5;

    case_strict_mock<int> int_case;

    EXPECT_CALL(int_case, call(5));
    op.match([&] (const int & i) { int_case.call(i); });
}

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
