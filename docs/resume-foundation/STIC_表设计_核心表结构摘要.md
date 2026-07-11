# STIC_AIGC 表设计核心摘要

> 提取自：`技术文档/技术文档/技术设计/数据表设计/STIC_AIGC_表设计_0829.xlsx`  
> 更新日期：2025-08-29

---

## 表清单（16张核心表）

| 表名 | 简称 | 描述 |
|------|------|------|
| `hhr_ta_basic_info` | 简历信息表 | 候选人简历主表，存储基本信息和原始文本 |
| `hhr_ta_category` | 标签分类表 | 标签分类体系（一级/二级分类） |
| `hhr_ta_cert` | 简历证书表 | 候选人证书/奖项 |
| `hhr_ta_education` | 简历教育经历表 | 教育背景 |
| `hhr_ta_job_exp` | 工作经历及实习经历表 | 工作/实习经历 |
| `hhr_ta_lang` | 语言证书表 | 语言技能 |
| `hhr_ta_position` | 岗位信息表 | 岗位JD信息 |
| `hhr_ta_position_recognition` | 岗位信息解析表 | 岗位JD解析结果 |
| `hhr_ta_proj_exp` | 项目经历表 | 项目经验 |
| `hhr_ta_resume_tags` | 简历标签表 | 简历标签（多对多关联） |
| `hhr_ta_skills` | 简历技能表 | 技能列表 |
| `hhr_ta_social_exp` | 社会经历表 | 社会实践 |
| `hhr_ta_tags` | 人才标签表 | 标签字典 |
| `hhr_ta_upload_history` | 简历上传历史表 | 上传批次记录 |
| `hhr_ta_upload_history_detail` | 简历上传历史明细表 | 上传文件明细 |
| `hhr_ta_position_find_record` | 人岗匹配查询记录表 | 匹配查询主表 |
| `hhr_ta_position_find_record_detail` | 人岗匹配查询记录明细表 | 匹配结果明细 |
| `hhr_ta_resume_keywords` | 简历关键词表 | 简历关键词 |
| `hhr_ta_organization` | 组织架构表 | MDM组织信息 |

---

## 核心表详细字段

### 1. `hhr_ta_basic_info` - 简历信息表

**核心字段（60+个）**

#### 基本信息
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `resume_code` | varchar(100) | 简历CODE（唯一索引） |
| `name` | varchar(60) | 候选人姓名 |
| `name_en` | varchar(100) | 英文名 |
| `gender` | varchar(10) | 性别（男/女） |
| `gender_inf` | varchar(10) | 性别(推断)，模型推断结果 |
| `age` | int | 年龄 |
| `age_inf` | int | 年龄(推断) |
| `marital_status` | varchar(20) | 婚姻状态 |
| `id_card` | varchar(50) | 身份证号 |
| `phone` | varchar(50) | 联系电话 |
| `email` | char(50) | 联系邮箱 |

#### 教育与职业
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `education` | varchar(50) | 最高学历 |
| `job_grade` | varchar(50) | 岗位级别 |
| `languages` | varchar(100) | 语言能力（逗号分隔） |
| `english_level` | varchar(20) | 英语水平 |
| `apply_job` | varchar(20) | 应聘职位 |

#### 工作相关
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `work_year` | varchar(20) | 工作年限 |
| `work_year_norm` | varchar(20) | 工作年限(规范) |
| `work_year_inf` | varchar(20) | 工作年限(推断) |
| `work_start_time` | varchar(20) | 参加工作时间 |
| `work_position` | varchar(20) | 当前职位 |
| `work_company` | varchar(50) | 当前单位 |
| `work_industry` | varchar(50) | 所处行业 |
| `work_status` | varchar(10) | 在职状态（在职/离职） |
| `work_location` | varchar(50) | 工作地点 |
| `work_salary` | varchar(50) | 当前薪资 |

#### 期望求职
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `expect_time` | varchar(50) | 到岗时间 |
| `expect_jlocation` | varchar(50) | 期望工作地点 |

#### 原始文本段落（cont_* 系列）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `cont_basic_info` | varchar(1000) | 原始简历基本信息段落 |
| `cont_expect_job` | varchar(1000) | 原始期望工作描述段落 |
| `cont_education` | varchar(1000) | 原始教育经历段落 |
| `cont_job_exp` | varchar(1000) | 原始工作经历段落 |
| `cont_internship` | varchar(1000) | 原始实习段落 |
| `cont_proj_exp` | varchar(1000) | 原始项目描述段落 |
| `cont_job_skill` | varchar(1000) | 原始技能段落 |
| `cont_my_desc` | varchar(1000) | 原始自我评价段落 |
| `cont_language` | varchar(1000) | 原始语言技能段落 |
| `cont_certificate` | varchar(1000) | 原始证书段落 |
| `cont_training` | longtext | 原始培训段落 |
| `cont_research` | longtext | 原始科研段落 |
| `cont_cover_letter` | longtext | 原始求职信段落 |
| `cont_extra_info` | longtext | 其他附加信息段落 |

#### 全文与元数据
| 字段名 | 类型 | 说明 |
|--------|------|------|
| `raw_text` | longtext | **完整原始简历文本** |
| `avatar_url` | varchar(500) | 头像URL |
| `resume_integrity` | varchar(10) | 简历完整度（0~100分） |
| `resume_source` | varchar(50) | 简历来源（智联/前程无忧/猎聘/boss直聘等） |
| `resume_high_light` | varchar(100) | 简历亮点 |
| `resume_risk` | varchar(100) | 简历风险点 |

#### 标准租户字段
- `tenant_id` - 租户ID
- `object_version_number` - 行版本号（乐观锁）
- `creation_date`, `created_by`, `last_update_date`, `last_updated_by`, `last_update_login`

**索引：**
- 唯一索引：`(tenant_id, id)`
- 唯一索引：`(resume_code)`

---

### 2. `hhr_ta_category` - 标签分类表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `category_name` | varchar(50) | 分类名称 |
| `parent_id` | bigint | 父分类ID（0=一级分类） |
| `is_enabled` | tinyint(1) | 启用状态（1=启用，0=失效） |

**索引：**
- 唯一索引：`(category_name)`

---

### 3. `hhr_ta_tags` - 人才标签表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `tag_name` | varchar(50) | 标签名称 |
| `category_id` | bigint | 所属分类ID |
| `is_enabled` | tinyint(1) | 启用状态 |

---

### 4. `hhr_ta_resume_tags` - 简历标签表（多对多关联）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `resume_id` | bigint | 关联简历ID |
| `tag_id` | bigint | 关联标签ID |
| `tag_value` | varchar(100) | 标签值 |
| `tag_weight` | decimal | 标签权重 |

---

### 5. `hhr_ta_resume_keywords` - 简历关键词表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `resume_id` | bigint | 关联简历ID |
| `candidate_type` | varchar(20) | 候选人类型（校招/社招） |
| `dimension` | varchar(50) | 关键词维度（专业技能/项目经验/工作经历等） |
| `keyword` | varchar(100) | 关键词内容 |
| `keyword_weight` | decimal | 关键词权重 |

---

### 6. `hhr_ta_upload_history` - 简历上传历史表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `upload_batch_code` | varchar(100) | 上传批次号 |
| `upload_time` | datetime | 上传时间 |
| `upload_user_id` | bigint | 上传人ID |
| `total_count` | int | 总数量 |
| `success_count` | int | 成功数量 |
| `fail_count` | int | 失败数量 |
| `status` | varchar(20) | 上传状态（成功/失败/部分成功/处理中） |

---

### 7. `hhr_ta_upload_history_detail` - 简历上传历史明细表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `upload_history_id` | bigint | 关联上传历史ID |
| `resume_file_name` | varchar(200) | 简历文件名 |
| `file_url` | varchar(500) | 文件URL |
| `parse_status` | varchar(20) | 解析状态（成功/失败/处理中） |
| `error_message` | text | 失败原因 |

---

### 8. `hhr_ta_position` - 岗位信息表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `position_code` | varchar(100) | 岗位编码 |
| `position_name` | varchar(100) | 岗位名称 |
| `department_id` | bigint | 所属部门ID |
| `work_location` | varchar(50) | 工作地点 |
| `position_duties` | longtext | 岗位职责（原文） |
| `position_requirements` | longtext | 岗位要求（原文） |
| `jd_vector` | blob | JD向量（embedding） |
| `status` | varchar(20) | 岗位状态（启用/停用/草稿） |

---

### 9. `hhr_ta_position_find_record` - 人岗匹配查询记录表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `position_id` | bigint | 岗位ID |
| `search_time` | datetime | 查询时间 |
| `search_user_id` | bigint | 查询人ID |
| `result_count` | int | 匹配候选人数量 |

---

### 10. `hhr_ta_position_find_record_detail` - 人岗匹配查询记录明细表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | bigint | 主键 |
| `find_record_id` | bigint | 关联查询记录ID |
| `resume_id` | bigint | 候选人简历ID |
| `match_score` | decimal(5,2) | 匹配度评分（0~100） |
| `semantic_score` | decimal(5,2) | 向量匹配分（权重50%） |
| `tag_score` | decimal(5,2) | 标签匹配分（权重30%） |
| `keyword_score` | decimal(5,2) | 关键词匹配分（权重20%） |
| `match_summary` | text | 匹配度总结（LLM生成） |
| `match_highlights` | text | 匹配亮点 |
| `match_risks` | text | 风险点 |

---

## 🔑 关键设计特点

### 1. 字段设计模式
- **原值 + 规范值 + 推断值**：如 `work_year`, `work_year_norm`, `work_year_inf`
  - 原值：简历原文
  - 规范值：系统标准化
  - 推断值：模型推断（当原文缺失时）

### 2. 原始文本分段存储
- `cont_*` 系列字段：按段落保存原始文本（基本信息/教育/工作/项目/技能/...）
- `raw_text`：完整原文（longtext）
- **设计目的**：支持 RAG 检索和人工回溯

### 3. 租户多租户架构
- 所有表都有 `tenant_id`
- 唯一索引都包含 `tenant_id`

### 4. 乐观锁
- `object_version_number` 字段用于并发控制

### 5. 向量字段
- `jd_vector`（岗位表）：预留 blob 类型存储 embedding
- 简历向量：表设计中未明确字段，可能存在 `hhr_ta_basic_info` 的扩展字段或单独向量表

---

## 📌 与另一个 Codex 技术设计的对应关系

| STIC 原始表 | Codex 设计底座表 | 对应程度 |
|-------------|-------------------|----------|
| `hhr_ta_basic_info` | `seeker_resumes` (当前简历指针) | ✅ 类似，但 Codex 拆得更细 |
| `hhr_ta_upload_history` + `detail` | `resume_uploads` | ✅ 完全对应 |
| 无 | `resume_parse_runs` | ❌ Codex 新增（解析任务状态机） |
| `raw_text` 字段 | `resume_extracted_texts` | ⚠️ Codex 独立表 + 质量分 |
| 无 | `resume_chunks` | ❌ Codex 新增（RAG chunk） |
| `cont_*` 分段 | `resume_chunks.section` | ⚠️ 思路相似，Codex 更结构化 |
| `hhr_ta_resume_tags` | `resume_tags` | ✅ 完全对应 |
| `hhr_ta_resume_keywords` | `resume_keywords` | ✅ 完全对应 |
| 结构化字段直接在 `basic_info` | `resume_structured_profiles` | ❌ Codex 独立表 + 确认机制 |
| 无 | `resume_profile_change_logs` | ❌ Codex 新增（回写日志） |

**关键差异**：
1. **STIC 表设计**：简历信息都塞在 `hhr_ta_basic_info` 一张大表（60+ 字段）
2. **Codex 底座设计**：按生命周期拆分（上传 → 解析 → 抽取 → chunk → 结构化 → 确认），每个环节独立表

---

## 🎯 建议

**如果基于 STIC 表设计实现简历解析底座**：

### 方案 A：最小改动（复用现有表）
- 保留 `hhr_ta_basic_info` 主表
- 新增 `parse_status`, `parse_run_id`, `upload_id` 字段
- 新增 `resume_parse_runs` 表（记录解析任务）
- 新增 `resume_chunks` 表（RAG）
- 用 `hhr_ta_upload_history_detail.parse_status` 追踪解析状态

### 方案 B：按 Codex 设计重构（推荐）
- 创建完整的 8 张底座表
- `hhr_ta_basic_info` 降级为"当前生效简历视图"或废弃
- 数据迁移：把现有 `hhr_ta_basic_info` 数据补到新表
- **好处**：清晰、可追溯、易扩展

---

**生成时间**：2026-06-15  
**数据来源**：STIC_AIGC_表设计_0829.xlsx
