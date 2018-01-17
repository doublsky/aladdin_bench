#include "fft.h"

#ifdef DMA_MODE
#include "gem5/dma_interface.h"
#endif

void fft(DTYPE real[FFT_SIZE], DTYPE img[FFT_SIZE],
         DTYPE real_twid[FFT_SIZE/2], DTYPE img_twid[FFT_SIZE/2]) {
    int even, odd, span, log, rootindex;
    DTYPE temp;

#ifdef DMA_MODE
    dmaLoad(&real[0], 0 * 512 * sizeof(DTYPE), 512 * sizeof(DTYPE));
    dmaLoad(&real[0], 1 * 512 * sizeof(DTYPE), 512 * sizeof(DTYPE));
    dmaLoad(&img[0], 0 * 512 * sizeof(DTYPE), 512 * sizeof(DTYPE));
    dmaLoad(&img[0], 1 * 512 * sizeof(DTYPE), 512 * sizeof(DTYPE));
    dmaLoad(&real_twid[0], 0, 512 * sizeof(DTYPE));
    dmaLoad(&img_twid[0], 0, 512 * sizeof(DTYPE));
#endif

    log = 0;

    outer:for(span=FFT_SIZE>>1; span; span>>=1, log++){
        inner:for(odd=span; odd<FFT_SIZE; odd++){
            odd |= span;
            even = odd ^ span;

            temp = real[even] + real[odd];
            real[odd] = real[even] - real[odd];
            real[even] = temp;

            temp = img[even] + img[odd];
            img[odd] = img[even] - img[odd];
            img[even] = temp;

            rootindex = (even<<log) & (FFT_SIZE - 1);
            if(rootindex){
                temp = real_twid[rootindex] * real[odd] -
                    img_twid[rootindex]  * img[odd];
                img[odd] = real_twid[rootindex]*img[odd] +
                    img_twid[rootindex]*real[odd];
                real[odd] = temp;
            }
        }
    }
#ifdef DMA_MODE
    dmaStore(&real[0], 0 * 512 * sizeof(DTYPE), 512 * sizeof(DTYPE));
    dmaStore(&real[0], 1 * 512 * sizeof(DTYPE), 512 * sizeof(DTYPE));
    dmaStore(&img[0], 0 * 512 * sizeof(DTYPE), 512 * sizeof(DTYPE));
    dmaStore(&img[0], 1 * 512 * sizeof(DTYPE), 512 * sizeof(DTYPE));
#endif
}
