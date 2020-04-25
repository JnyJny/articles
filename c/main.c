
#include <stdio.h>		/* Standard I/O, printf and friends */
#include <stdlib.h>		/* EXIT_FAILURE, EXIT_SUCCESS */
#include <libgen.h>		/* basename */
#include <errno.h>		/*  */
#include <getopt.h>		/* getopt(3c) */
#include <string.h>		/* string and mem functions */

extern char *optarg;		/* external symbols from libc */
extern int   opterr;

#define OPTSTR "vf:n:"

int dump_file(FILE *filep, FILE *output);

int main(int argc, char *argv[])
{
  int opt;
  int verbose = 0;
  int number = 0;
  FILE *fp = NULL;

  opterr = 0;

  while((opt = getopt(argc, argv, OPTSTR))!= EOF)
    switch(opt) {
      case 'v':
	verbose ++;
	break;
      case 'f':
	if (fp)
	  fclose(fp);
	if (!(fp=fopen(optarg,"r"))) {
	  perror("-f: error opening file");
	  exit(EXIT_FAILURE);
	}
	break;
      case 'n':
	number = strtoul(optarg, NULL, 10);
	break;
      case 'h':
      case '?':
      default:
	fprintf(stderr, "usage: %s [-v]|[-f filename][-n integer]\n",
		basename(argv[0]));
	exit(EXIT_FAILURE);
	/* NOTREACHED */
    }

  printf("verbose = %d\n", verbose);
  printf("number  = %d\n", number);

  if (dump_file(fp, stdout) < 0 ){
    perror("dump_file");
    exit(EXIT_FAILURE);
  }
    
  return EXIT_SUCCESS;
}


int dump_file(FILE *filep, FILE *output)
{
  char buf[80];
  
  if (!filep) {
    errno = EINVAL;
    return -1;
  }

  while (fgets(buf, sizeof(buf)-1, filep)) {
    fputs(buf, output);
  }
    
  return 0;
}
