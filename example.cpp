#include "option.hpp"

#include <iostream>

int main()
{
    option i;

    i = 1;

    i.match([] (int i)
            {
                std::cout << "have int: " << i << std::endl;
            },
            [] (std::string s)
            {
                std::cout << "have string: " << s << std::endl;
            });
}
