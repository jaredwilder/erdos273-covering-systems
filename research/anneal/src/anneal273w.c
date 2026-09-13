/* anneal273.c -- compiled bitset/count local search for covering systems of Z/N
 *
 * Erdos 273, hard half B: find residues r_m (one per modulus m in the pool)
 * such that the classes r_m mod m cover every residue of Z/N.
 *
 * Pool modes:
 *   --auto            pool = { m : m | N, m >= 2, 2m+1 prime }  minus {2}   (the HARD half)
 *   --auto2           pool = { m : m | N, m >= 2, 2m+1 prime }  including 2 (control 1, N=180)
 *   --pool a,b,c,...  explicit pool (control 2, Krukenberg Z/144)
 *
 * Every pool modulus is USED (a residue is always assigned).  This is WLOG:
 * if a subset covers, assigning arbitrary residues to the rest still covers.
 *
 * Objective: number of uncovered residues of Z/N.  Moves: reassign one modulus's
 * residue to the class that covers the most currently-uncovered points
 * (delta-evaluated over an explicit uncovered list), tabu on the modulus index,
 * WalkSAT-style noise, perturbation on stall, full restart on deep stall.
 *
 * Symmetry: modulus 3 is frozen at residue 0 (translation invariance), unless --nofix3.
 *
 * Build:  gcc -O3 -march=native -o anneal273 anneal273.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

/* ---------------- rng ---------------- */
static uint64_t rs = 88172645463325252ULL;
static inline uint64_t rnd64(void){ rs^=rs<<13; rs^=rs>>7; rs^=rs<<17; return rs; }
static inline int rndint(int n){ return (int)(rnd64() % (uint64_t)n); }
static inline double rnd01(void){ return (double)(rnd64()>>11) * (1.0/9007199254740992.0); }

/* ---------------- state ---------------- */
static int N, K;
static int pool[4096];
static int cur[4096], bestv[4096];
static long long tabu_until[4096];
static int frozen[4096];

static unsigned char *cnt;      /* coverage multiplicity per residue */
static int32_t *ulist, *upos;   /* uncovered set, swap-remove indexed */
static int un;
static int32_t *zc, *touched;
static int32_t *wt;      /* PAWS-style point weights */
static long long bumps=0;

static inline void udel(int j){ int p=upos[j]; int last=ulist[--un]; ulist[p]=last; upos[last]=p; upos[j]=-1; }
static inline void uadd(int j){ upos[j]=un; ulist[un++]=j; }

static void addm(int m,int r){ for(int j=r;j<N;j+=m){ if(cnt[j]++==0) udel(j); } }
static void delm(int m,int r){ for(int j=r;j<N;j+=m){ if(--cnt[j]==0) uadd(j); } }

/* best residue for modulus m, assuming m's class has already been removed.
   returns the class covering the most uncovered points; *gain = that count. */
static int best_residue(int m, int *gain, double noise){
  int nt=0;
  for(int i=0;i<un;i++){ int u=ulist[i]; int c = u%m; if(zc[c]==0) touched[nt++]=c; zc[c]+=wt[u]; }
  if(nt==0){ *gain=0; return rndint(m); }
  int pick;
  if(noise>0.0 && rnd01()<noise){
    pick = touched[rndint(nt)];              /* random class that covers >=1 uncovered */
    *gain = zc[pick];
  } else {
    int bg=-1, bc=touched[0], ties=0;
    for(int i=0;i<nt;i++){ int c=touched[i];
      if(zc[c]>bg){ bg=zc[c]; bc=c; ties=1; }
      else if(zc[c]==bg){ ties++; if(rndint(ties)==0) bc=c; } }
    pick=bc; *gain=bg;
  }
  for(int i=0;i<nt;i++) zc[touched[i]]=0;
  return pick;
}

static int isprime(long long n){
  if(n<2) return 0;
  if(n%2==0) return n==2;
  for(long long d=3; d*d<=n; d+=2) if(n%d==0) return 0;
  return 1;
}

static void fresh_state(void){
  memset(cnt,0,(size_t)N);
  un=0; for(int j=0;j<N;j++){ ulist[j]=j; upos[j]=j; } un=N;
  for(int i=0;i<K;i++){ cur[i] = frozen[i] ? 0 : rndint(pool[i]); addm(pool[i],cur[i]); }
  /* one greedy sweep */
  for(int i=0;i<K;i++){
    if(frozen[i]) continue;
    delm(pool[i],cur[i]);
    int g; int r=best_residue(pool[i],&g,0.0);
    addm(pool[i],r); cur[i]=r;
  }
}

int main(int argc,char**argv){
  int mode=0;              /* 0 auto(hard), 1 auto2(with 2), 2 explicit */
  char explicit_pool[8192]; explicit_pool[0]=0;
  long long seed=12345; double secs=600; const char*prefix="run"; int fix3=1;
  double log_every=30.0, noise=0.15;
  long long stall_mult=400;
  const char*qlock="(none)";

  for(int a=1;a<argc;a++){
    if(!strcmp(argv[a],"--N")) N=atoi(argv[++a]);
    else if(!strcmp(argv[a],"--auto")) mode=0;
    else if(!strcmp(argv[a],"--auto2")) mode=1;
    else if(!strcmp(argv[a],"--pool")){ mode=2; strncpy(explicit_pool,argv[++a],8191); }
    else if(!strcmp(argv[a],"--seed")) seed=atoll(argv[++a]);
    else if(!strcmp(argv[a],"--secs")) secs=atof(argv[++a]);
    else if(!strcmp(argv[a],"--out")) prefix=argv[++a];
    else if(!strcmp(argv[a],"--nofix3")) fix3=0;
    else if(!strcmp(argv[a],"--noise")) noise=atof(argv[++a]);
    else if(!strcmp(argv[a],"--log-every")) log_every=atof(argv[++a]);
    else if(!strcmp(argv[a],"--stall-mult")) stall_mult=atoll(argv[++a]);
    else if(!strcmp(argv[a],"--question-lock")) qlock=argv[++a];
    else { fprintf(stderr,"unknown arg %s\n",argv[a]); return 2; }
  }
  if(N<=0){ fprintf(stderr,"need --N\n"); return 2; }
  rs = (uint64_t)seed*6364136223846793005ULL + 1442695040888963407ULL;
  for(int i=0;i<20;i++) rnd64();

  K=0;
  if(mode==2){
    char*p=explicit_pool; char*tok=strtok(p,",");
    while(tok){ pool[K++]=atoi(tok); tok=strtok(NULL,","); }
  } else {
    for(int m=2;m<=N;m++) if(N%m==0 && isprime(2LL*m+1)){
      if(mode==0 && m==2) continue;
      pool[K++]=m;
    }
  }
  if(K==0){ fprintf(stderr,"empty pool\n"); return 2; }

  double S=0; for(int i=0;i<K;i++) S+=1.0/pool[i];

  cnt     = malloc((size_t)N);
  ulist   = malloc(sizeof(int32_t)*(size_t)N);
  upos    = malloc(sizeof(int32_t)*(size_t)N);
  zc      = calloc((size_t)N,sizeof(int32_t));
  touched = malloc(sizeof(int32_t)*(size_t)N);
  wt      = malloc(sizeof(int32_t)*(size_t)N);
  if(wt) for(int j=0;j<N;j++) wt[j]=1;
  if(!cnt||!ulist||!upos||!zc||!touched||!wt){ fprintf(stderr,"oom\n"); return 3; }

  for(int i=0;i<K;i++){ frozen[i] = (fix3 && pool[i]==3) ? 1 : 0; tabu_until[i]=0; }

  char logf[1024], witf[1024], bestf[1024];
  snprintf(logf ,1023,"%s.log",prefix);
  snprintf(witf ,1023,"%s.WITNESS.json",prefix);
  snprintf(bestf,1023,"%s.best.json",prefix);
  FILE*L=fopen(logf,"w");
  if(!L) L=stderr;
  fprintf(L,"# anneal273w(WEIGHTED) N=%d K=%d S=%.6f seed=%lld secs=%.0f noise=%.2f fix3=%d\n",N,K,S,seed,secs,noise,fix3);
  fprintf(L,"# question-lock: %s",qlock); fputc(10,L);
  fprintf(L,"# pool:"); for(int i=0;i<K;i++) fprintf(L," %d",pool[i]); fprintf(L,"\n");
  fprintf(L,"# NOTE: S<=1 means the pool cannot cover -- density floor.\n");
  fflush(L);

  clock_t t0=clock();
  double tlast=0;
  int global_best=N+1;
  long long iter=0, last_improve=0, restarts=0, perturbs=0;
  long long stall = stall_mult*(long long)K;
  long long deep  = 60*stall;
  long long last_restart=0;
  long long bump_period = (long long)K*2;
  long long last_bump=0; 
  int run_best=N+1;

  fresh_state();
  run_best=un;
  if(un<global_best){ global_best=un; memcpy(bestv,cur,sizeof(int)*K); }

  while(1){
    iter++;
    /* pick a modulus index: prefer non-tabu, non-frozen */
    int i=-1;
    for(int t=0;t<32;t++){ int c=rndint(K); if(frozen[c]) continue; if(tabu_until[c]<=iter){ i=c; break; } if(i<0) i=c; }
    if(i<0||frozen[i]){ continue; }

    delm(pool[i],cur[i]);
    int g; int r=best_residue(pool[i],&g,noise);
    addm(pool[i],r); cur[i]=r;
    tabu_until[i] = iter + (long long)(K/2 + rndint(K/2+1));

    if(un<run_best){ run_best=un; last_improve=iter; }
    if(un<global_best){
      global_best=un; memcpy(bestv,cur,sizeof(int)*K);
      FILE*B=fopen(bestf,"w");
      if(B){ fprintf(B,"{\"N\":%d,\"uncovered\":%d,\"iter\":%lld,\"pairs\":[",N,un,iter);
        for(int q=0;q<K;q++) fprintf(B,"%s[%d,%d]",q?",":"",cur[q],pool[q]);
        fprintf(B,"]}\n"); fclose(B); }
    }

    if(un==0){
      double el=(double)(clock()-t0)/CLOCKS_PER_SEC;
      FILE*W=fopen(witf,"w");
      if(W){
        fprintf(W,"{\n \"result\":\"WITNESS\",\n \"N\":%d,\n \"K\":%d,\n \"density\":%.6f,\n \"seed\":%lld,\n \"iters\":%lld,\n \"seconds\":%.2f,\n \"pairs\":[",N,K,S,seed,iter,el);
        for(int q=0;q<K;q++) fprintf(W,"%s[%d,%d]",q?",":"",cur[q],pool[q]);
        fprintf(W,"],\n \"human\":\"");
        for(int q=0;q<K;q++) fprintf(W,"%s%d mod %d",q?"; ":"",cur[q],pool[q]);
        fprintf(W,"\"\n}\n"); fclose(W);
      }
      fprintf(L,"WITNESS iter=%lld secs=%.2f\n",iter,el);
      for(int q=0;q<K;q++) fprintf(L,"%d mod %d\n",cur[q],pool[q]);
      fflush(L);
      printf("WITNESS FOUND N=%d seed=%lld iter=%lld\n",N,seed,iter);
      fclose(L);
      return 0;
    }

    if((iter&1023)==0){
      double el=(double)(clock()-t0)/CLOCKS_PER_SEC;
      if(el-tlast>=log_every){
        tlast=el;
        fprintf(L,"t=%.0f iter=%lld cur=%d run_best=%d global_best=%d restarts=%lld perturbs=%lld\n",
                el,iter,un,run_best,global_best,restarts,perturbs);
        fflush(L);
      }
      if(el>=secs){
        fprintf(L,"STOP t=%.0f iter=%lld global_best=%d restarts=%lld perturbs=%lld\n",el,iter,global_best,restarts,perturbs);
        fprintf(L,"RESULT NO_WITNESS_FOUND_LOCAL_SEARCH N=%d seed=%lld best_uncovered=%d seconds=%.1f iters=%lld\n",
                N,seed,global_best,el,iter);
        fflush(L); fclose(L);
        printf("NOWITNESS N=%d seed=%lld best=%d\n",N,seed,global_best);
        return 1;
      }
    }

    if(un>0 && iter-last_improve > bump_period && iter-last_bump > bump_period){
      for(int q=0;q<un;q++) wt[ulist[q]]++;
      bumps++;
      if((bumps & 2047)==0){ for(int j=0;j<N;j++) wt[j] = 1 + wt[j]/2; }
      last_bump=iter;
    }
    if(iter-last_improve > stall){
      if(iter-last_restart > deep){
        fresh_state(); run_best=un; last_improve=iter; last_restart=iter; restarts++;
        for(int j=0;j<N;j++) wt[j]=1;
        for(int q=0;q<K;q++) tabu_until[q]=0;
      } else {
        int p = 1 + K/8;
        for(int q=0;q<p;q++){
          int c=rndint(K); if(frozen[c]) continue;
          delm(pool[c],cur[c]); int nr=rndint(pool[c]); addm(pool[c],nr); cur[c]=nr;
        }
        run_best=un; last_improve=iter; perturbs++;
      }
    }
  }
}
