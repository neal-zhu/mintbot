# free mint bot

一个 demo 级别的 free mint 机器人，参考打狗神器 [mycointool](https://mycointool.com/nft/minting)

## 依赖
1. redis(存储模块使用)

使用前请在本机安装 redis，如需使用远程 redis，自己修改 ``mintbot/storage.py`` 中的 redis 初始化配置


## 运行
```shell
# 推荐使用 venv 管理, 在 main.py 中写入自己的 API_KEY 以后
pip isntall -r requirements.txt
python main.py
```

## TODO
1. 性能优化，可行方向有：
    * 在合约创建后就开始进行 verify 相关操作，并且将结果写入 redis，这样可以节省处理最新 block 时的性能开销
    * 每个 block 都并发处理，防止阻塞对新块的处理
    * 储备 API_KEY 池，避免 etherscan 等外部依赖的限速问题
2. 配置化
3. 前端展示
4. 优雅退出