#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <libavcodec/avcodec.h>
#define F(ret,name,args) static ret (*p_##name) args
F(unsigned,avcodec_version,(void));
F(const AVCodec*,avcodec_find_decoder_by_name,(const char*));
F(AVCodecContext*,avcodec_alloc_context3,(const AVCodec*));
F(int,avcodec_open2,(AVCodecContext*,const AVCodec*,AVDictionary**));
F(AVCodecParserContext*,av_parser_init,(int));
F(int,av_parser_parse2,(AVCodecParserContext*,AVCodecContext*,uint8_t**,int*,const uint8_t*,int,int64_t,int64_t,int64_t));
F(AVPacket*,av_packet_alloc,(void));
F(AVFrame*,av_frame_alloc,(void));
F(int,avcodec_send_packet,(AVCodecContext*,const AVPacket*));
F(int,avcodec_receive_frame,(AVCodecContext*,AVFrame*));
static long frames,samples;
static void drain(AVCodecContext*c,AVFrame*f){int r;while((r=p_avcodec_receive_frame(c,f))>=0){frames++;samples+=f->nb_samples;}if(r!=AVERROR(EAGAIN)&&r!=AVERROR_EOF)exit(5);}
static void decode(const char*path,const char*name){const AVCodec*d=p_avcodec_find_decoder_by_name(name);AVCodecContext*c=p_avcodec_alloc_context3(d);if(p_avcodec_open2(c,d,NULL)<0)exit(3);AVCodecParserContext*p=p_av_parser_init(d->id);AVPacket*pkt=p_av_packet_alloc();AVFrame*f=p_av_frame_alloc();FILE*in=fopen(path,"rb");fseek(in,0,SEEK_END);long size=ftell(in);rewind(in);uint8_t*b=calloc(1,size+AV_INPUT_BUFFER_PADDING_SIZE);if(fread(b,1,size,in)!=size)exit(4);uint8_t*cur=b;frames=samples=0;while(size>0){int n=p_av_parser_parse2(p,c,&pkt->data,&pkt->size,cur,size,AV_NOPTS_VALUE,AV_NOPTS_VALUE,0);if(n<0||(!n&&!pkt->size))exit(4);cur+=n;size-=n;if(pkt->size){if(p_avcodec_send_packet(c,pkt)<0)exit(5);drain(c,f);}}p_av_parser_parse2(p,c,&pkt->data,&pkt->size,NULL,0,AV_NOPTS_VALUE,AV_NOPTS_VALUE,0);if(pkt->size){if(p_avcodec_send_packet(c,pkt)<0)exit(5);drain(c,f);}if(p_avcodec_send_packet(c,NULL)<0)exit(5);drain(c,f);printf("%s frames=%ld samples=%ld rate=%d channels=%d\n",name,frames,samples,c->sample_rate,c->ch_layout.nb_channels);}
int main(int argc,char**argv){void*h=dlopen("libavcodec.so.61",RTLD_NOW|RTLD_LOCAL);if(!h){puts(dlerror());return 1;}
#define LOAD(n) do{*(void**)(&p_##n)=dlsym(h,#n);if(!p_##n)return 2;}while(0)
LOAD(avcodec_version);LOAD(avcodec_find_decoder_by_name);LOAD(avcodec_alloc_context3);LOAD(avcodec_open2);LOAD(av_parser_init);LOAD(av_parser_parse2);LOAD(av_packet_alloc);LOAD(av_frame_alloc);LOAD(avcodec_send_packet);LOAD(avcodec_receive_frame);
if(p_avcodec_version()!=0x3d1365)return 2;printf("version=61.19.101\n");const char*names[]={"aac","h264","hevc","vp8","vp9","vp6f"};for(int i=0;i<6;i++){if(!p_avcodec_find_decoder_by_name(names[i]))return 2;printf("decoder=%s\n",names[i]);}decode(argv[1],"h264");decode(argv[2],"aac");FILE*m=fopen("/proc/self/maps","r");char line[4096];while(fgets(line,sizeof(line),m))fputs(line,stdout);return 0;}
