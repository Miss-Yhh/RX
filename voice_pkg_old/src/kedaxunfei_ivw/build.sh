gcc -c linuxrec.c
g++ -g -std=c++11 -o microphone microphone.cpp linuxrec.o -L./libs/ -laikit -lpthread -ldl -Wl,-rpath=lib -lasound
