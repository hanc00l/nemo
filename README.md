# Nemo

Nemo是用来进行自动化信息收集的一个简单平台，实现对内网及互联网资产信息的自动收集，提高隐患排查和渗透测试的工作效率。



# 功能

## IP收集

- Nmap、Masscan端口扫描
- 第三方接口查询IP归属地（hao7188、ip.cn）、自定义IP归属地

## 域名收集

- [Sublist3r](https://github.com/aboul3la/Sublist3r)
- [Subfinder](https://github.com/projectdiscovery/subfinder)
- 子域名爆破（修改版[ESD](https://github.com/FeeiCN/ESD)）
- [JSFinder](https://github.com/Threezh1/JSFinder)

## 标题指纹

- [WhatWeb](https://github.com/urbanadventurer/WhatWeb)
- [HTTPX](https://github.com/projectdiscovery/httpx)

## API接口

- [Fofa](https://fofa.so/)
- [Shodan](https://www.shodan.io/)

## Poc验证

- [Pocsuite3](https://github.com/knownsec/pocsuite3)（[some_pocsuite](https://github.com/hanc00l/some_pocsuite)）
- [XRay](https://github.com/chaitin/xray)

## 其它

- 资产的导出、统计、颜色标记与备忘录协作
- Celery实现分布式任务
- Docker部署和运行



# 安装

[开发环境配置](docs/config.md)

[MacOS安装配置](docs/install_mac.md)



# Docker

```shell
git clone --recursive https://github.com/hanc00l/nemo
cd nemo
docker build  -t nemo/app:v1 .
docker run -it -d --name nemo_app -p 5000:5000 nemo/app:v1
```



# 使用

浏览器输入 [http://localhost:5000](http://localhost:5000)，默认用户名密码：**nemo/nemo**


<img src="docs/login.jpg" alt="login" />

<img src="docs/dashbord.jpg" alt="dashbord"  />



# 版本更新

- 0.2：2021-2-8，增加子域名收集Subfinder、JSFinder，增加标题指纹HTTPX；重构任务相关代码；
- 0.1：2021-2-3，重构任务管理功能，集成Pocsuite3与XRay进行验洞验证；



# 参考

jeffzh3ng：https://github.com/jeffzh3ng/fuxi

TideSec：https://github.com/TideSec/Mars