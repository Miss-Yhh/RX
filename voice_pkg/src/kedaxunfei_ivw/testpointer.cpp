#include <iostream>
using namespace std;
int main(int argc, char const *argv[])
{
    int a = 10;
    int* p1 = new int;
    *p1 = 1478;
    cout << *p1 << endl;
    int* p2 = p1;
    cout << p2 << endl;
    delete p1;
    return 0;
}
