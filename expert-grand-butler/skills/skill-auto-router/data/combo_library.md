# 技能调用记忆库（自动生成）

> 更新时间：2026-09-15 09:23:30　|　累计 0 次任务记录　|　0 个技能被调用过　|　0 个任务类型

## 一、预置组合（已晋级，同类任务可走快速通道）

_暂无。同一任务类型的调用链重复达到阈值后会自动出现在这里。_

## 二、试用中的组合（次数未达晋级阈值）

_暂无。_

## 三、高频技能 Top 0

_暂无记录。_

## 四、强关联技能对 Top 0

_暂无记录。_

## 五、如何喂养这个记忆库

每次任务收尾执行一次（`skills` 按实际调用顺序填写）：

```bash
python scripts/record_usage.py --task-type "任务类型" \
    --forms word,ppt --skills "技能A,技能B,技能C" --success true
```

查看统计：`python scripts/record_usage.py --stats`　|　删除某类记忆：`python scripts/record_usage.py --forget "任务类型"`