#include "bb_gemm.h"

#ifdef DMA_MODE
#include "gem5/dma_interface.h"
#endif

void bb_gemm(double x[N], double y[N], double z[N]){
#ifdef DMA_MODE
  dmaLoad(&x[0], 0, ROWSIZE*BLOCKSIZE*sizeof(double));
  dmaLoad(&y[0], 0, BLOCKSIZE*BLOCKSIZE*sizeof(double));
  dmaLoad(&z[0], 0, ROWSIZE*BLOCKSIZE*sizeof(double));
#endif
  int i, k, j;
  double temp_x;
	loopi:for ( i = 0; i < ROWSIZE; ++i){
		loopk:for (k = 0; k < BLOCKSIZE; ++k){
	      		temp_x = x[i * ROWSIZE + k];
			loopj:for (j = 0; j < BLOCKSIZE; ++j){
	      			z[i * ROWSIZE + j] += temp_x * y[k*ROWSIZE + j];
      			}

      		}
	}
#ifdef DMA_MODE
	dmaStore(&z[0], 0, ROWSIZE*BLOCKSIZE*sizeof(double));
#endif
}
void print(double *a, int size)
{
	int i;

	for (i = 0; i < size; i++)
		printf("%f\t", a[i]);
}

int main()
{
	int i;
  double  *x;
  double *y;
  double *z;
  x = (double*) malloc(sizeof(double) * N); //ROWSIZE * BLOCKSIZE
  y = (double*) malloc(sizeof(double) * N); //BLOCKSIZE * BLOCKSIZE
  z = (double*) malloc(sizeof(double) * N);

  double max, min;
	srand(8650341L);
  max = 128;
  min = 0;
  for(i=0; i<N; i++){
    x[i] = (TYPE)(((double) rand() / (RAND_MAX)) * (max-min) + min);
    y[i] = (TYPE)(((double) rand() / (RAND_MAX)) * (max-min) + min);
    z[i] = 0;
  }

#ifdef GEM5
  resetGem5Stats();
#endif
	bb_gemm(x, y, z);
#ifdef GEM5
  dumpGem5Stats("bb_gemm");
#endif
  print(z, N);
	printf("\n");

	return 0;
}

