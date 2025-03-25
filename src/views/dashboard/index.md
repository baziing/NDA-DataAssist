# 自动报表
### I 快速入门
1. 导入模块：[下载模版示例](https://gitee.com/jhzkkk/downloads/raw/master/neo/%E6%A8%A1%E7%89%88%E7%A4%BA%E4%BE%8B.xlsx) 
- db_name（必填）：sql运行数据库
- output_sql（必填）：运行的sql，支持变量替换。将需要替换的字符前后分别插入"{"和"}"。
- format：表格样式规则，具体见样式规则（见自动报表-格式说明）。
- pos：表格之间的相对位置
- transpose(Y/N)：表格是否倒置
2. 导入变量：[下载变量示例](https://gitee.com/jhzkkk/downloads/raw/master/neo/%E5%8F%98%E9%87%8F%E7%A4%BA%E4%BE%8B.xlsx)
点击`SKIP`则会代表无需替换变量/清空变量。
点击`上传`则会解析上传文件，解析成功则会显示会替换变量。
- key（必填）：需要替换的变量，`key`必须唯一。
- value（必填）：替换内容
3. 开始执行&下载结果
### II 其他功能
[功能展示示例](https://gitee.com/jhzkkk/downloads/raw/master/neo/%E9%A3%8E%E5%A4%A7%E7%94%9F%E6%80%81.xlsx) 
1. 支持多页签导入。不同页签sql会分别导入至对应页签。
2. 支持sql合并。由于excel一个单元格最多只能放下32767个字符，所以需要对sql进行拆分再组合。可以插入sql1/sql2/...字段，处理的时候会自动将 output_sql+sql1+sql2+... 代码合并处理。
3. 支持冻结功能。新建一个{setting}页签，需要有三个字段fun/title/config。
- fun（功能）：目前仅支持“冻结”。
- title（页签）：适用的页签。
- config（配置）：
  - 当fun=冻结时，config可以为单元格(B2)/行(2)/列(B)，以该所有范围为中心进行冻结。