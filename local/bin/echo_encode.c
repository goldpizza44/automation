#include <stdio.h>
main(argc,argv)
int argc;
char *argv[];

{
int c;
int char_in_line;
int lines;
char echostring[20];

strcpy(echostring,"echo -e  \"");

while ((c = getopt(argc, argv, "l")) != EOF ) {
	switch(c)
	{
	case 'l': /* Linux echo style */
		strcpy(echostring,"/bin/echo -e  \"");			
		break;
	}
}

char_in_line=0;
while ( (c=getc(stdin)) != EOF) {

	if ( char_in_line == 0) printf(echostring);

	
	if ( (c >= 'a' && c <= 'z') || 
	     (c >= 'A' && c <= 'Z') ||
              c == '!' || c == '#'  ||
              c == '*' || c == '='  ||
              c == '(' || c == '|'  ||
              c == ')' || c == '{'  ||
              c == '+' || c == '}'  ||
              c == '-' || c == '['  ||
              c == '_' || c == ']'  ||
              c == ':' || c == ';'  ||
              c == ',' || c == '.'  ||
              c == '<' || c == '>'
	) {
		putchar(c);
		char_in_line++;
	} else if (c >= 0100) {
		printf("\\\\%04o",c);
		char_in_line+=5;
	} else {
		printf("\\\\%03o",c);
		char_in_line+=4;
	}
	if (char_in_line > 50) {
		printf("\\\\c\"\n");
		char_in_line = 0;
		lines++;
	}
}
printf("\\\\c\"\n");
lines++;


}
