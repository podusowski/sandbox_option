#pragma once

#include <functional>
#include <typeinfo>

template<class Signature>
struct arg_type : public arg_type<decltype(&Signature::operator())>
{
};

template<class Result, class Class, class Arg>
struct arg_type<Result(Class::*)(Arg) const>
{
    typedef Arg type;
};

template<class Result, class Class, class Arg>
struct arg_type<Result(Class::*)(Arg)>
{
    typedef Arg type;
};

template<class Result, class Arg>
struct arg_type<Result(*)(Arg)>
{
    typedef Arg type;
};

template<class T>
struct clear_case_type
{
    using type = typename std::remove_reference<typename arg_type<T>::type>::type;
};

struct option
{
    using deleter_type = std::function<void()>;

    option()
    {
    }

    template<class T>
    option(T value)
    {
        *this = value;
    }

    ~option()
    {
        clear();
    }

    template<class T>
    option & operator = (T && value)
    {
        clear();

        using base_type = typename std::remove_reference<T>::type;

        static_assert(!std::is_array<base_type>::value, "arrays, except c-strings, are not supported");

        type = &typeid(base_type);
        storage = new base_type(std::forward<T>(value));
        deleter = [this] { delete reinterpret_cast<base_type*>(storage); };

        return *this;
    }

    template<class First, class... Others>
    void match(First first, Others... others) const
    {
        using arg_t = typename clear_case_type<First>::type;

        if (&typeid(arg_t) == type)
        {
            first(get_unsafe<arg_t>());
        }
        else
        {
            this->match(others...);
        }
    }

    template<class First>
    void match(First first) const
    {
        using arg_t = typename clear_case_type<First>::type;

        if (&typeid(arg_t) == type)
        {
            first(get_unsafe<arg_t>());
        }
    }

private:
    template<class T>
    auto get_unsafe() const -> T
    {
        return *reinterpret_cast<T*>(storage);
    }

    void clear()
    {
        if (storage)
        {
            deleter();
        }
    }

    deleter_type deleter;
    void * storage = nullptr;
    std::type_info const * type = nullptr;
};
