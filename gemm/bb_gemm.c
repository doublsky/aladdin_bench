#include "bb_gemm.h"

#ifdef DMA_MODE
#include "gem5/dma_interface.h"
#endif

void bb_gemm(int x[N], int y[N], int z[N]){
#ifdef DMA_MODE
  dmaLoad(&x[0], 0, (N)*sizeof(int));
  dmaLoad(&y[0], 0, (N)*sizeof(int));
  dmaLoad(&z[0], 0, (N)*sizeof(int));
#endif
  int i, k, j, temp_x;
	loopi:for ( i = 0; i < (BLOCKSIZE); ++i){
		loopk:for (k = 0; k < (BLOCKSIZE); ++k){
	      		temp_x = x[i * (BLOCKSIZE) + k];
			loopj:for (j = 0; j < BLOCKSIZE; ++j){
	      			z[i * (BLOCKSIZE) + j] += temp_x * y[k*(BLOCKSIZE) + j];
      			}

      		}
	}
#ifdef DMA_MODE
	dmaStore(&z[0], 0, (N)*sizeof(int));
#endif
}
void print(int *a, int size)
{
	int i;

	for (i = 0; i < size; i++)
		printf("%u\t", a[i]);
}

int main()
{
	int i;
  int  *x;
  int *y;
  int *z;
  x = (int*) malloc(sizeof(int) * N); //ROWSIZE * BLOCKSIZE
  y = (int*) malloc(sizeof(int) * N); //BLOCKSIZE * BLOCKSIZE
  z = (int*) malloc(sizeof(int) * N);

  int max, min;
	srand(8650341L);
  max = 1000000000;
  min = -1000000000;
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

