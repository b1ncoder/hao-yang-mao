window.SEC_SERVER = {
  "rows": [
    [
      "Cloady",
      "免费区美西 / 美东",
      "搭备用节点",
      {
        "t": "只有 0.3 核 / 256MB 内存；出口是机房 IP、Cloudflare 风险系数高；晚上速度一般",
        "bad": true
      }
    ],
    [
      "Vortexa",
      "免费档 Node.js / Java 计划",
      "等补货领机",
      {
        "t": "Java 计划无 SSH、只能跑 Java；Node.js 经常无货；保活规则未核实",
        "bad": true
      }
    ],
    [
      "ASCS",
      "免费机 1 核 / 512MB / 16GB",
      "等补货领机",
      {
        "t": "每 30 天要续期一次；补货先到先得，抢不到就没货",
        "bad": true
      }
    ],
    [
      "Serv00",
      "免费共享主机",
      "轻量挂机",
      {
        "t": "不是 VPS、无 root；注册需人工审核（最多 72 小时）；需定期登录保活",
        "bad": true
      }
    ],
    [
      "VPSWala",
      "$0 Starter，免绑卡",
      "等开通",
      {
        "t": "开通要人工审核、无明确时限；条款要求公司邮箱",
        "bad": true
      }
    ],
    [
      "Railway",
      "每月 $1 额度",
      "临时跑小服务",
      {
        "t": "做不了 24/7 常驻；$1 只够约 50MB 内存；服务必须休眠",
        "bad": true
      }
    ],
    [
      "InstaBox",
      "免费 1 台 4 核 8GB / 20GB",
      "临时或备用节点",
      {
        "t": "无独立公网 IPv4、IPv6 入站不通、REALITY 不可用；闲置 30 分钟暂停、最长连跑 8 小时",
        "bad": true
      }
    ],
    [
      "InfinityFree",
      "永久免费虚拟主机，5GB 空间",
      "搭静态页",
      {
        "t": "无 SSH / root；自订域名要改 NS，部分免费域名接不进来",
        "bad": true
      }
    ],
    [
      {
        "t": "Oracle Cloud Always Free",
        "u": "https://www.oracle.com/cloud/free/",
        "tag": {
          "text": "长期免费",
          "cls": "ok"
        }
      },
      "Ampere A1 免费实例 + 2 台 AMD 微型实例 + 200GB 存储",
      "常驻小服务",
      {
        "t": "须绑卡 + 手机验证；热门区常无容量；闲置可能回收",
        "bad": true
      }
    ],
    [
      {
        "t": "GCP Always Free",
        "u": "https://cloud.google.com/free",
        "tag": {
          "text": "长期免费",
          "cls": "ok"
        }
      },
      "每月 1 台 e2-micro、30GB 盘、1GB 出站",
      "常驻小服务",
      {
        "t": "须绑卡；仅限美西 / 美中 / 美东三区；超量按卡计费",
        "bad": true
      }
    ]
  ]
};
