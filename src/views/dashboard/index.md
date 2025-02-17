# 自动报表
## 手动生成
### I 使用教程
1. 导入模块：[下载模版示例](https://gitee.com/jhzkkk/downloads/raw/master/neo/%E6%A8%A1%E7%89%88%E7%A4%BA%E4%BE%8B.xlsx) 
- db_name（必填）：sql运行数据库
- output_sql（必填）：运行的sql，支持变量替换。将需要替换的字符前后分别插入"{"和"}"。
- format：表格样式规则，具体见样式规则（见自动报表-使用说明）。
- pos：表格之间的相对位置
- transpose(Y/N)：表格是否倒置
2. 导入变量：[下载变量示例](https://gitee.com/jhzkkk/downloads/raw/master/neo/%E5%8F%98%E9%87%8F%E7%A4%BA%E4%BE%8B.xlsx)
点击`SKIP`则会代表无需替换变量/清空变量。
点击`上传`则会解析上传文件，解析成功则会显示会替换变量。
- key（必填）：需要替换的变量，`key`必须唯一。
- value（必填）：替换内容
3. 开始执行&下载结果
# 后续计划
1. 添加定时配置
2. 添加邮件配置