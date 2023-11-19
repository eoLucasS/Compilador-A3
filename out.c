#include <stdio.h>
void main(void){
float Loop;
float PrimeiroNum;
float Operador;
float SegundoNum;
float Result;
Loop = 1;
while(Loop==1){
printf("Calculadora em BASIC\n");
printf("Escreva o Primeiro Digito\n");
if(0 == scanf("%f", &PrimeiroNum)) {
PrimeiroNum = 0;
scanf("%*s");
}
printf("Escolha o Operador Matematico\n");
printf("+ -> 1\n");
printf("- -> 2\n");
printf("* -> 3\n");
printf("/ -> 4\n");
if(0 == scanf("%f", &Operador)) {
Operador = 0;
scanf("%*s");
}
printf("Escreva o Segundo Digito\n");
if(0 == scanf("%f", &SegundoNum)) {
SegundoNum = 0;
scanf("%*s");
}
if(Operador==1){
Result = PrimeiroNum+SegundoNum;
printf("%.2f\n", (float)(Result));
}
if(Operador==2){
Result = PrimeiroNum-SegundoNum;
printf("%.2f\n", (float)(Result));
}
if(Operador==3){
Result = PrimeiroNum*SegundoNum;
printf("%.2f\n", (float)(Result));
}
if(Operador==4){
Result = PrimeiroNum/SegundoNum;
printf("%.2f\n", (float)(Result));
}
}
return;
}
