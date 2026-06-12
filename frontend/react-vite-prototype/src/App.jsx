import React, { useState, useCallback, useContext, createContext } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate, useParams } from 'react-router-dom';
import {
  LayoutDashboard, Briefcase, MessageSquare, BarChart3, Users, Search,
  Plus, Bell, Settings, FileCheck, Shield, Activity, Zap, TrendingUp,
  Eye, Send, Star, BookmarkPlus, MapPin, Clock, Building2, ChevronRight,
  ArrowUpRight, ArrowDownRight, Filter, MoreHorizontal, CheckCircle2,
  AlertTriangle, XCircle, Bot, Sparkles, UserCircle, Home, Heart,
  Inbox, User, Menu, X, ChevronDown, ThumbsUp, Upload, Paperclip,
  Bookmark, ArrowLeft, Loader2, FileSpreadsheet, Download, FileText, Trash2
} from 'lucide-react';
import {
  Card, Table, Tag, Button, Input, Select, Tabs, Progress, Switch,
  Tooltip, Avatar, Badge, Steps, Radio, Checkbox, Space, Modal,
  message as antMessage, Upload as AntUpload, notification, Drawer
} from 'antd';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as ReTooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts';

/* ============================================================
   GLOBAL STATE CONTEXT
   ============================================================ */
const AppState = createContext();

const initialJobs = [
  { key: 1, name: '前端开发工程师', city: '深圳·南山区', salary: '15K-25K', status: 'online', views: 328, msgs: 12, date: '2026-05-28' },
  { key: 2, name: 'Java开发工程师', city: '深圳·福田区', salary: '18K-30K', status: 'online', views: 256, msgs: 8, date: '2026-05-25' },
  { key: 3, name: 'UI设计师', city: '广州·天河区', salary: '10K-18K', status: 'online', views: 189, msgs: 6, date: '2026-05-22' },
  { key: 4, name: '产品经理', city: '深圳·南山区', salary: '20K-35K', status: 'pending', views: 0, msgs: 0, date: '2026-06-01' },
  { key: 5, name: '销售经理', city: '广州·番禺区', salary: '8K-15K+提成', status: 'online', views: 145, msgs: 3, date: '2026-05-15' },
  { key: 6, name: '数据分析师', city: '深圳·南山区', salary: '15K-25K', status: 'pending', views: 0, msgs: 0, date: '2026-06-02' },
  { key: 7, name: '运维工程师', city: '深圳·南山区', salary: '12K-20K', status: 'closed', views: 98, msgs: 2, date: '2026-04-10' },
];

const initialConversations = [
  { id: 1, name: '张伟', job: '前端开发工程师', preview: '您好，我对这个岗位非常感兴趣，请问什么...', time: '10:23', unread: 2, emotion: 'high',
    messages: [
      { from: 'them', text: '您好，我对贵公司的前端开发工程师岗位非常感兴趣。我有5年React开发经验，目前在一家互联网公司担任前端技术负责人，希望了解更多关于团队技术栈和项目情况的信息。', time: '10:15', emotion: 'high' },
      { from: 'me', text: '张伟您好！感谢您的关注。我们团队目前使用React + TypeScript技术栈，主要服务于B端SaaS产品。团队规模8人，正在扩展核心模块的架构升级。', time: '10:20' },
      { from: 'them', text: '听起来很不错！请问什么时候方便安排一次深入沟通？我对贵公司的产品方向很感兴趣，也希望能了解团队的开发流程。', time: '10:23', emotion: 'high', isInterview: true },
    ]
  },
  { id: 2, name: '王丽华', job: '前端开发工程师', preview: '感谢回复，我想了解更多关于团队技术栈的...', time: '09:45', unread: 1, emotion: 'high',
    messages: [
      { from: 'them', text: '您好，看到贵公司的前端开发岗位，觉得非常匹配。我在上家公司做了3年Vue开发，也有React项目经验。', time: '09:30', emotion: 'high' },
      { from: 'me', text: '王丽华您好，感谢您的关注！Vue和React双栈经验在我们团队是很受欢迎的。请问您对B端产品有了解吗？', time: '09:38' },
      { from: 'them', text: '感谢回复，我想了解更多关于团队技术栈的细节，以及是否有Vue相关的项目？', time: '09:45', emotion: 'high' },
    ]
  },
  { id: 3, name: '陈思', job: 'Java开发工程师', preview: '请问这个岗位支持远程办公吗？', time: '昨天', unread: 0, emotion: 'medium',
    messages: [
      { from: 'them', text: '您好，我目前在成都，看到贵公司在深圳的Java开发岗位。请问这个岗位支持远程办公吗？', time: '昨天 14:20', emotion: 'medium' },
    ]
  },
  { id: 4, name: '刘洋', job: 'UI设计师', preview: '好的，我已经提交了作品集链接', time: '昨天', unread: 0, emotion: 'medium',
    messages: [
      { from: 'them', text: '您好，我对UI设计师岗位很感兴趣，我有4年B端设计经验。', time: '前天 16:00', emotion: 'medium' },
      { from: 'me', text: '刘洋您好，欢迎！方便分享一下您的作品集吗？', time: '前天 16:30' },
      { from: 'them', text: '好的，我已经提交了作品集链接，请查收。', time: '昨天 09:10', emotion: 'medium' },
    ]
  },
  { id: 5, name: '赵敏', job: '销售经理', preview: '请问底薪和提成的比例是怎样的？', time: '2天前', unread: 0, emotion: 'low',
    messages: [
      { from: 'them', text: '你好，请问销售经理岗位的底薪和提成的比例是怎样的？', time: '2天前 11:00', emotion: 'low' },
    ]
  },
];

const seekerConversations = [
  { id: 101, name: '李明辉（星辰互联）', job: '高级前端开发工程师', jobId: 1, preview: '可以安排本周四下午2点线上面试...', time: '10:20', unread: 1, isInterview: true,
    messages: [
      { from: 'me', text: '您好，我对高级前端开发工程师岗位非常感兴趣，有5年React开发经验。', time: '昨天 15:00' },
      { from: 'them', text: '您好！您的背景很匹配我们的需求。我们团队使用React+TypeScript技术栈，您有兴趣进一步了解吗？', time: '昨天 15:30' },
      { from: 'me', text: '非常感兴趣！请问什么时候方便安排一次深入沟通？', time: '昨天 16:00' },
      { from: 'them', text: '可以安排本周四下午2点线上面试，时长约45分钟。请确认时间是否方便，我会发送会议邀请。', time: '10:20', isInterview: true },
    ]
  },
  { id: 102, name: '王经理（云创数据）', job: 'Java后端开发工程师', jobId: 2, preview: '感谢您的留言，我们的技术栈主要是...', time: '昨天', unread: 1, isInterview: false,
    messages: [
      { from: 'me', text: '您好，我对Java后端岗位感兴趣，请问团队技术栈是什么？', time: '前天 10:00' },
      { from: 'them', text: '感谢您的留言，我们的技术栈主要是Spring Boot + MySQL + Redis + Kafka，团队20人左右。', time: '昨天 09:00' },
    ]
  },
];

const AppProvider = ({ children }) => {
  const [jobs, setJobs] = useState(initialJobs);
  const [recruiterConversations, setRecruiterConversations] = useState(initialConversations);
  const [seekerConvos, setSeekerConvos] = useState(seekerConversations);
  const [favorites, setFavorites] = useState(new Set());
  const [subscriptions, setSubscriptions] = useState([
    { id: 1, keywords: ['前端开发', 'React', 'Web开发'], city: '深圳', salary: '15K+', active: true },
    { id: 2, keywords: ['UI设计', 'Figma', 'B端设计'], city: '深圳, 广州', salary: '10K+', active: true },
    { id: 3, keywords: ['产品经理', 'B端', 'SaaS'], city: '不限', salary: '15K-25K', active: false },
  ]);
  const [reviewItems, setReviewItems] = useState([
    { id: 1, type: '企业资质', company: '深圳市创新科技有限公司', submitter: '王晓明', time: '10:35', status: 'pending', aiResult: 'pass', aiNote: 'AI预审通过，OCR验证一致' },
    { id: 2, type: '岗位内容', company: '广州云创数据', job: '高薪诚聘全栈工程师', submitter: '张经理', time: '09:48', status: 'warning', aiResult: 'warning', aiNote: 'AI检测到歧视性用语："仅限男性"' },
    { id: 3, type: '企业资质', company: '深圳XX金融集团', submitter: '陈某', time: '09:12', status: 'blocked', aiResult: 'block', aiNote: 'AI初筛命中假冒企业风险：信用代码与企业名不匹配' },
    { id: 4, type: '岗位内容', company: '杭州灵感设计科技', job: 'UI设计师', submitter: '李芳', time: '昨天', status: 'pending', aiResult: 'pass', aiNote: 'AI预审通过，内容合规' },
  ]);
  const [currentRole, setCurrentRole] = useState('recruiter');

  const toggleFavorite = (id) => {
    setFavorites(prev => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); antMessage.info('已取消收藏'); }
      else { next.add(id); antMessage.success('已收藏职位'); }
      return next;
    });
  };

  const addRecruiterMessage = (convId, text) => {
    setRecruiterConversations(prev => prev.map(c =>
      c.id === convId ? { ...c, messages: [...c.messages, { from: 'me', text, time: '刚刚' }], unread: 0 } : c
    ));
  };

  const addSeekerMessage = (convId, text) => {
    setSeekerConvos(prev => prev.map(c =>
      c.id === convId ? { ...c, messages: [...c.messages, { from: 'me', text, time: '刚刚' }] } : c
    ));
  };

  const toggleSubscription = (id) => {
    setSubscriptions(prev => prev.map(s => s.id === id ? { ...s, active: !s.active } : s));
  };

  const removeSubscription = (id) => {
    setSubscriptions(prev => prev.filter(s => s.id !== id));
    antMessage.success('已删除订阅');
  };

  const addSubscription = (sub) => {
    setSubscriptions(prev => [...prev, { ...sub, id: Date.now(), active: true }]);
    antMessage.success('订阅创建成功');
  };

  const closeJob = (key) => {
    setJobs(prev => prev.map(j => j.key === key ? { ...j, status: 'closed' } : j));
    antMessage.success('岗位已下架');
  };

  const reopenJob = (key) => {
    setJobs(prev => prev.map(j => j.key === key ? { ...j, status: 'online' } : j));
    antMessage.success('岗位已重新上线');
  };

  const approveReview = (id) => {
    setReviewItems(prev => prev.filter(r => r.id !== id));
    notification.success({ message: '审核通过', description: '已通知相关用户', placement: 'topRight' });
  };

  const rejectReview = (id) => {
    setReviewItems(prev => prev.filter(r => r.id !== id));
    notification.warning({ message: '审核不通过', description: '已通知用户修改并重新提交', placement: 'topRight' });
  };

  return (
    <AppState.Provider value={{
      jobs, setJobs, recruiterConversations, addRecruiterMessage,
      seekerConvos, addSeekerMessage, favorites, toggleFavorite,
      subscriptions, toggleSubscription, removeSubscription, addSubscription,
      closeJob, reopenJob, reviewItems, approveReview, rejectReview,
      currentRole, setCurrentRole
    }}>
      {children}
    </AppState.Provider>
  );
};

/* ============================================================
   SHARED COMPONENTS
   ============================================================ */
const AIBadge = ({ children, variant = 'default' }) => (
  <span className={`ai-badge ${variant === 'solid' ? 'ai-badge--solid' : variant === 'outline' ? 'ai-badge--outline' : ''}`}>
    <Sparkles size={10} /> {children}
  </span>
);

const AIBtn = ({ children, onClick, loading }) => (
  <button className="ai-btn" onClick={onClick} disabled={loading} style={{ opacity: loading ? 0.6 : 1 }}>
    {loading ? <Loader2 size={14} className="ai-loading" /> : <Sparkles size={14} />} {loading ? '生成中...' : children}
  </button>
);

const StatCard = ({ icon, label, value, delta, deltaType, color = 'var(--color-primary)', onClick }) => (
  <div className="stat-card" data-component="StatCard" onClick={onClick} style={onClick ? { cursor: 'pointer' } : {}}>
    <div className="stat-card__label">
      <span style={{ color, display: 'flex' }}>{icon}</span>{label}
    </div>
    <div className="stat-card__value">{value}</div>
    {delta && (
      <span className={`stat-card__delta stat-card__delta--${deltaType}`}>
        {deltaType === 'up' ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}{delta}
      </span>
    )}
  </div>
);

const EmotionTag = ({ level }) => {
  const map = { high: '高意向', medium: '一般', low: '仅咨询' };
  return <span className={`emotion-tag emotion-tag--${level}`}>{map[level]}</span>;
};

const StatusBadge = ({ status, label }) => (
  <span className={`status-badge status-badge--${status} status-badge--dot`}>{label}</span>
);

/* ============================================================
   SIDEBAR LAYOUT (with navigate)
   ============================================================ */
const SidebarLayout = ({ brand, nav, children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  return (
    <div className="dashboard-layout" data-component="SidebarLayout">
      <aside className="sidebar" data-component="Sidebar">
        <div className="sidebar__brand">
          <div className="sidebar__brand-icon"><Briefcase size={18} /></div>
          <span className="sidebar__brand-text">{brand}</span>
        </div>
        <nav className="sidebar__nav">
          {nav.map((section, i) => (
            <div className="sidebar__section" key={i}>
              {section.title && <div className="sidebar__section-title">{section.title}</div>}
              {section.items.map(item => (
                <a key={item.path + item.label}
                  className={`sidebar__link ${location.pathname === item.path ? 'sidebar__link--active' : ''}`}
                  onClick={(e) => { e.preventDefault(); navigate(item.path); }}>
                  {item.icon}<span>{item.label}</span>
                  {item.badge && <span className="sidebar__link-badge">{item.badge}</span>}
                </a>
              ))}
            </div>
          ))}
        </nav>
        <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-light)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Avatar size={32} style={{ background: 'var(--color-primary)', fontSize: 13 }}>李</Avatar>
            <div>
              <div style={{ fontSize: 13, fontWeight: 510 }}>李明辉</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>深圳锐智科技有限公司</div>
            </div>
          </div>
        </div>
      </aside>
      <main className="content-area">{children}</main>
    </div>
  );
};

/* ============================================================
   RECRUITER PAGES (with interactions)
   ============================================================ */
const trendData = [
  { day: '周一', views: 128, messages: 12 },
  { day: '周二', views: 156, messages: 18 },
  { day: '周三', views: 203, messages: 24 },
  { day: '周四', views: 187, messages: 15 },
  { day: '周五', views: 245, messages: 31 },
  { day: '周六', views: 98, messages: 8 },
  { day: '周日', views: 76, messages: 5 },
];

const RecruiterDashboard = () => {
  const navigate = useNavigate();
  return (
    <div className="fade-in" data-component="RecruiterDashboard">
      <div className="content-header">
        <h2 className="content-header__title">工作台</h2>
        <p className="content-header__subtitle">欢迎回来，李明辉。以下是您的招聘概览。</p>
      </div>

      <div className="stats-grid" data-component="StatsGrid">
        <StatCard icon={<Briefcase size={16} />} label="在线岗位" value="12" delta="+3 本周新增" deltaType="up" onClick={() => navigate('/recruiter/jobs')} />
        <StatCard icon={<Eye size={16} />} label="本周浏览量" value="1,093" delta="+23.5% vs 上周" deltaType="up" color="var(--color-accent)" />
        <StatCard icon={<MessageSquare size={16} />} label="未读消息" value="7" delta="3 高意向" deltaType="up" color="var(--color-success)" onClick={() => navigate('/recruiter/messages')} />
        <StatCard icon={<FileCheck size={16} />} label="审核中" value="2" delta="预计24h内完成" deltaType="up" color="var(--color-warning)" />
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="chart-card" data-component="TrendChart">
          <div className="chart-card__title">近7日岗位表现趋势</div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="day" tick={{ fontSize: 12, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} />
              <ReTooltip contentStyle={{ borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13 }} />
              <Area type="monotone" dataKey="views" stroke="var(--color-primary)" fill="var(--color-primary-soft)" strokeWidth={2} name="浏览量" />
              <Area type="monotone" dataKey="messages" stroke="var(--color-accent)" fill="var(--color-accent-soft)" strokeWidth={2} name="留言数" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="insight-card" data-component="TodoPanel">
          <div className="insight-card__header"><Bell size={18} color="var(--color-primary)" /><h4 style={{ margin: 0 }}>待办事项</h4></div>
          {[
            { icon: <CheckCircle2 size={18} />, color: 'var(--color-success-soft)', iconColor: 'var(--color-success)', title: '「UI设计师」审核通过', desc: '岗位已上线，开始接收应聘者留言', time: '10分钟前', action: () => navigate('/recruiter/jobs') },
            { icon: <MessageSquare size={18} />, color: 'var(--color-primary-soft)', iconColor: 'var(--color-primary)', title: '3条新留言待回复', desc: '张伟、王丽华、陈思对「前端开发工程师」留言', time: '25分钟前', action: () => navigate('/recruiter/messages') },
            { icon: <AlertTriangle size={18} />, color: 'var(--color-warning-soft)', iconColor: 'var(--color-warning)', title: '「销售经理」岗位即将到期', desc: '有效期剩余7天，请及时续期或下架', time: '2小时前', action: () => navigate('/recruiter/jobs') },
            { icon: <Sparkles size={18} />, color: 'var(--color-accent-soft)', iconColor: 'var(--color-accent)', title: 'AI洞察：薪资建议更新', desc: '「Java开发工程师」上海市场薪资区间已更新为18K-30K', time: '今天', action: () => navigate('/recruiter/job/create') },
          ].map((item, i) => (
            <div className="todo-item" key={i} onClick={item.action}>
              <div className="todo-item__icon" style={{ background: item.color, color: item.iconColor }}>{item.icon}</div>
              <div className="todo-item__content">
                <div className="todo-item__title">{item.title}</div>
                <div className="todo-item__desc">{item.desc}</div>
              </div>
              <span className="todo-item__time">{item.time}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="insight-card" data-component="AIInsightPanel">
        <div className="insight-card__header"><Sparkles size={18} color="var(--color-accent)" /><h4 style={{ margin: 0 }}>AI 智能洞察</h4><AIBadge>AI分析</AIBadge></div>
        {[
          { title: '「前端开发工程师」浏览量高但留言偏少', desc: '该岗位本周浏览328次但仅收到4条留言（互动率1.2%），可能原因：薪资范围低于市场P50水平。建议参考同类岗位调整至15K-25K区间，并使用AI润色优化岗位描述吸引力。', action: () => navigate('/recruiter/job/create') },
          { title: '「Java开发工程师」发布时间可优化', desc: '数据显示工作日上午9-10点发布的岗位平均多获得35%的首日曝光。建议将新岗位安排在该时段提交。', action: () => navigate('/recruiter/job/create') },
        ].map((item, i) => (
          <div className="insight-item" key={i} style={{ cursor: 'pointer' }} onClick={item.action}>
            <div className="insight-item__title">{item.title} <ChevronRight size={14} style={{ verticalAlign: 'middle' }} /></div>
            <div className="insight-item__desc">{item.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

/* --- Recruiter Job Create (Interactive) --- */
const RecruiterJobCreate = () => {
  const navigate = useNavigate();
  const { setJobs } = useContext(AppState);
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    name: '前端开发工程师', cities: ['深圳', '广州'], salaryMin: '15000', salaryMax: '25000',
    salaryType: '月薪', responsibility: '', requirement: '',
  });
  const [aiWriting, setAiWriting] = useState(false);
  const [aiPolishing, setAiPolishing] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const steps = ['基本信息', '薪资设置', '职责要求', '公开设置', '预览提交'];

  const handleAIWrite = (field) => {
    setAiWriting(true);
    setTimeout(() => {
      if (field === 'responsibility') {
        setFormData(prev => ({ ...prev, responsibility: '1. 负责公司核心产品的前端架构设计与开发，确保系统高性能、高可用\n2. 主导前端技术选型，制定前端开发规范和代码标准\n3. 与产品经理、UI设计师紧密协作，将产品需求转化为高质量的技术实现\n4. 优化前端页面性能，提升用户体验，确保跨端兼容性\n5. 指导和培养初中级前端工程师，组织技术分享和代码评审\n6. 关注前端技术发展趋势，推动团队技术创新和工具链升级' }));
        antMessage.success('AI已生成工作职责');
      }
      setAiWriting(false);
    }, 1500);
  };

  const handleAIPolish = () => {
    if (!formData.responsibility) { antMessage.warning('请先输入或生成内容后再使用AI润色'); return; }
    setAiPolishing(true);
    setTimeout(() => {
      setFormData(prev => ({ ...prev, responsibility: prev.responsibility.replace(/负责/g, '全面负责').replace(/制定/g, '主导制定').replace(/协作/g, '深度协作') }));
      antMessage.success('AI润色完成');
      setAiPolishing(false);
    }, 1200);
  };

  const handleSubmit = () => {
    setSubmitting(true);
    setTimeout(() => {
      setJobs(prev => [{
        key: Date.now(), name: formData.name, city: formData.cities.join('、'),
        salary: `${formData.salaryMin/1000}K-${formData.salaryMax/1000}K`,
        status: 'pending', views: 0, msgs: 0, date: new Date().toISOString().split('T')[0]
      }, ...prev]);
      notification.success({ message: '岗位已提交审核', description: '预计24小时内完成审核，届时将通过微信通知您', placement: 'topRight' });
      setSubmitting(false);
      navigate('/recruiter/jobs');
    }, 1000);
  };

  const handleSaveDraft = () => {
    antMessage.success('草稿已保存');
  };

  return (
    <div className="fade-in" data-component="RecruiterJobCreate">
      <div className="content-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 className="content-header__title">发布新岗位</h2>
            <p className="content-header__subtitle">填写岗位信息，AI助手将帮助您提升招聘效果</p>
          </div>
          <Space>
            <Button onClick={handleSaveDraft}>保存草稿</Button>
            <Button type="primary" icon={<Send size={14} />} onClick={handleSubmit} loading={submitting}>提交发布</Button>
          </Space>
        </div>
      </div>

      <Steps current={currentStep} size="small" style={{ marginBottom: 24, maxWidth: 600 }}
        items={steps.map(s => ({ title: s }))}
        onChange={(c) => setCurrentStep(c)} />

      <div style={{ maxWidth: 720 }}>
        {currentStep === 0 && (
          <>
            <div className="form-section" data-component="JobNameField">
              <div className="form-section__title">岗位名称</div>
              <div className="form-field-label">请输入或从标准职位库选择 <AIBadge variant="outline">AI标准化</AIBadge></div>
              <Input size="large" value={formData.name} onChange={e => setFormData(p => ({...p, name: e.target.value}))} placeholder="如：输入「程序员」，AI推荐「软件开发工程师」" />
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
                {['前端开发工程师', 'Web开发工程师', '前端架构师'].map(t => (
                  <Tag key={t} color="blue" style={{ cursor: 'pointer' }} onClick={() => setFormData(p => ({...p, name: t}))}>{t}</Tag>
                ))}
              </div>
            </div>
            <div className="form-section">
              <div className="form-section__title">工作城市</div>
              <Select mode="multiple" size="large" value={formData.cities} onChange={v => setFormData(p => ({...p, cities: v}))}
                placeholder="选择工作城市（最多10个）" style={{ width: '100%' }}
                options={['深圳','广州','北京','上海','杭州','成都','武汉','南京'].map(c => ({ label: c, value: c }))} />
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <Button type="primary" onClick={() => setCurrentStep(1)}>下一步：薪资设置</Button>
            </div>
          </>
        )}

        {currentStep === 1 && (
          <>
            <div className="form-section">
              <div className="form-section__title">薪资待遇</div>
              <div className="ai-suggestion-bar">
                <Sparkles size={16} color="var(--color-accent)" />
                <span className="ai-suggestion-bar__text">AI建议：「{formData.name}」在{formData.cities[0] || '深圳'}的市场薪资区间为 12,000 - 22,000 元/月</span>
                <button className="ai-suggestion-bar__action" onClick={() => setFormData(p => ({...p, salaryMin: '12000', salaryMax: '22000'}))}>采用AI建议</button>
              </div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <Input size="large" value={formData.salaryMin} onChange={e => setFormData(p => ({...p, salaryMin: e.target.value}))} placeholder="最低薪资" />
                <span style={{ color: 'var(--text-tertiary)' }}>—</span>
                <Input size="large" value={formData.salaryMax} onChange={e => setFormData(p => ({...p, salaryMax: e.target.value}))} placeholder="最高薪资" />
                <Select size="large" value={formData.salaryType} onChange={v => setFormData(p => ({...p, salaryType: v}))} style={{ width: 100 }}
                  options={[{ label: '月薪', value: '月薪' }, { label: '年薪', value: '年薪' }]} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <Button onClick={() => setCurrentStep(0)}>上一步</Button>
              <Button type="primary" onClick={() => setCurrentStep(2)}>下一步：职责要求</Button>
            </div>
          </>
        )}

        {currentStep === 2 && (
          <>
            <div className="form-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="form-section__title" style={{ marginBottom: 0 }}>工作职责</div>
                <Space>
                  <AIBtn onClick={() => handleAIWrite('responsibility')} loading={aiWriting}>AI 代写</AIBtn>
                  <AIBtn onClick={handleAIPolish} loading={aiPolishing}>AI 润色</AIBtn>
                </Space>
              </div>
              <div style={{ marginTop: 12, position: 'relative' }} className={formData.responsibility ? 'ai-generated' : ''}>
                <Input.TextArea rows={8} value={formData.responsibility}
                  onChange={e => setFormData(p => ({...p, responsibility: e.target.value}))}
                  placeholder="请描述工作职责，或点击「AI代写」自动生成..." style={{ fontSize: 14, lineHeight: 1.7 }} />
              </div>
              <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                  {formData.responsibility && <><Sparkles size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />AI生成，请根据实际情况修改</>}
                </span>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{formData.responsibility.length}/2000字</span>
              </div>
            </div>
            <div className="form-section">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="form-section__title" style={{ marginBottom: 0 }}>任职要求</div>
                <AIBtn onClick={() => setFormData(p => ({...p, requirement: '1. 本科及以上学历，计算机科学或相关专业优先\n2. 3年以上前端开发经验，有大型项目交付经验\n3. 精通React或Vue框架，熟悉其生态系统和最佳实践\n4. 熟悉TypeScript，具备良好的代码规范和架构设计能力\n5. 良好的团队协作和沟通能力'}))}>AI 推荐</AIBtn>
              </div>
              <div style={{ marginTop: 12 }}>
                <div style={{ marginBottom: 12, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: '28px' }}>AI推荐要求：</span>
                  {['本科及以上学历', '3年以上前端开发经验', '精通React/Vue框架', '熟悉TypeScript', '良好的团队协作能力'].map(tag => (
                    <Tag key={tag} style={{ cursor: 'pointer' }} onClick={() => {
                      setFormData(p => ({ ...p, requirement: p.requirement + '\n- ' + tag }));
                      antMessage.success(`已添加：${tag}`);
                    }}>+ {tag}</Tag>
                  ))}
                </div>
                <Input.TextArea rows={5} value={formData.requirement}
                  onChange={e => setFormData(p => ({...p, requirement: e.target.value}))}
                  placeholder="请描述任职要求..." style={{ fontSize: 14, lineHeight: 1.7 }} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <Button onClick={() => setCurrentStep(1)}>上一步</Button>
              <Button type="primary" onClick={() => setCurrentStep(3)}>下一步：公开设置</Button>
            </div>
          </>
        )}

        {currentStep === 3 && (
          <>
            <div className="form-section">
              <div className="form-section__title">公开信息设置</div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>选择对外展示的信息，保护您的隐私</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border-light)' }}>
                  <div><div style={{ fontWeight: 510 }}>企业名称展示</div><div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>选择展示真名或虚拟名</div></div>
                  <Radio.Group defaultValue="virtual"><Radio value="real">企业真名</Radio><Radio value="virtual">虚拟名</Radio></Radio.Group>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid var(--border-light)' }}>
                  <div><div style={{ fontWeight: 510 }}>联系人展示</div><div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>选择展示真姓名或虚拟名</div></div>
                  <Radio.Group defaultValue="virtual"><Radio value="real">真姓名</Radio><Radio value="virtual">虚拟名</Radio></Radio.Group>
                </div>
                <div style={{ padding: '12px 0' }}>
                  <div style={{ fontWeight: 510, marginBottom: 8 }}>联系方式可见性</div>
                  <Checkbox.Group defaultValue={['email']} options={[
                    { label: '手机号', value: 'phone' }, { label: '微信号', value: 'wechat' }, { label: '企业邮箱', value: 'email' },
                  ]} />
                  <div style={{ fontSize: 12, color: 'var(--color-warning)', marginTop: 6 }}>至少需公开一项联系方式</div>
                </div>
              </div>
            </div>
            <div className="ai-review-panel ai-review-panel--warning" style={{ marginTop: 16 }}>
              <div className="ai-review-panel__header"><Sparkles size={16} color="var(--color-warning)" /><span style={{ color: 'var(--color-warning)' }}>AI 内容预审结果 — 警告</span><AIBadge>AI审核</AIBadge></div>
              <div className="ai-review-panel__item"><AlertTriangle size={14} color="var(--color-warning)" style={{ marginTop: 2, flexShrink: 0 }} />
                <span>建议优化：任职要求中"本科及以上学历"可调整为"学历不限"或添加"能力突出者可放宽"以增加候选人覆盖面。</span>
              </div>
              <div style={{ marginTop: 8 }}><Space><Button size="small" type="primary" style={{ background: 'var(--color-warning)', borderColor: 'var(--color-warning)' }}>查看修改建议</Button><Button size="small" onClick={() => setCurrentStep(4)}>继续</Button></Space></div>
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <Button onClick={() => setCurrentStep(2)}>上一步</Button>
              <Button type="primary" onClick={() => setCurrentStep(4)}>下一步：预览</Button>
            </div>
          </>
        )}

        {currentStep === 4 && (
          <>
            <div className="form-section">
              <div className="form-section__title">发布预览（应聘者视角）</div>
              <div style={{ background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)', padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 590 }}>{formData.name || '未填写岗位名称'}</div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>星辰互联（虚拟名）· {formData.cities.join('、')}</div>
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 590, color: 'var(--color-primary)' }}>
                    {formData.salaryMin ? `${formData.salaryMin/1000}K` : '?'}-{formData.salaryMax ? `${formData.salaryMax/1000}K` : '?'}
                  </div>
                </div>
                {formData.responsibility && (
                  <div style={{ marginTop: 16, fontSize: 13, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>工作职责：</strong><br/>{formData.responsibility}
                  </div>
                )}
                {formData.requirement && (
                  <div style={{ marginTop: 16, fontSize: 13, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                    <strong style={{ color: 'var(--text-primary)' }}>任职要求：</strong><br/>{formData.requirement}
                  </div>
                )}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <Button onClick={() => setCurrentStep(3)}>上一步</Button>
              <Button type="primary" icon={<Send size={14} />} onClick={handleSubmit} loading={submitting}>确认提交发布</Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

/* --- Recruiter Messages (Interactive) --- */
const RecruiterMessages = () => {
  const { recruiterConversations, addRecruiterMessage } = useContext(AppState);
  const [activeId, setActiveId] = useState(recruiterConversations[0]?.id);
  const [replyText, setReplyText] = useState('');
  const [showReplies, setShowReplies] = useState(true);

  const activeConv = recruiterConversations.find(c => c.id === activeId);

  const handleSend = () => {
    if (!replyText.trim()) return;
    addRecruiterMessage(activeId, replyText);
    setReplyText('');
    antMessage.success('回复已发送');
  };

  const handleAIReply = (text) => {
    addRecruiterMessage(activeId, text);
    setShowReplies(false);
    antMessage.success('已发送AI建议回复');
  };

  return (
    <div className="fade-in" data-component="RecruiterMessages">
      <div className="content-header">
        <h2 className="content-header__title">消息互动中心</h2>
        <p className="content-header__subtitle">管理应聘者留言，AI助您高效回复</p>
      </div>
      <div className="message-layout">
        <div className="message-list">
          <div className="message-list__header">全部消息 <Badge count={recruiterConversations.reduce((a, c) => a + c.unread, 0)} style={{ marginLeft: 8 }} /></div>
          <div className="message-list__items">
            {recruiterConversations.map(c => (
              <div key={c.id} className={`message-list__item ${c.id === activeId ? 'message-list__item--active' : ''}`} onClick={() => { setActiveId(c.id); setShowReplies(true); }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div className="message-list__item-name">{c.name} <EmotionTag level={c.emotion} /></div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{c.job}</div>
                  </div>
                  <span className="message-list__item-time">{c.time}</span>
                </div>
                <div className="message-list__item-preview" style={{ marginTop: 4 }}>{c.preview}</div>
                {c.unread > 0 && <Badge count={c.unread} style={{ marginTop: 4 }} />}
              </div>
            ))}
          </div>
        </div>

        {activeConv ? (
          <div className="message-thread">
            <div className="message-thread__header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <Avatar size={36} style={{ background: 'var(--color-primary)' }}>{activeConv.name[0]}</Avatar>
                <div>
                  <div style={{ fontWeight: 590, fontSize: 15 }}>{activeConv.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>应聘：{activeConv.job} · <EmotionTag level={activeConv.emotion} /></div>
                </div>
              </div>
              <Tooltip title="查看AI分析的简历亮点"><Button size="small" icon={<UserCircle size={14} />}>简历亮点</Button></Tooltip>
            </div>

            <div className="message-thread__messages">
              {activeConv.messages.map((m, i) => (
                <div key={i}>
                  <div className={`message-bubble message-bubble--${m.from === 'me' ? 'outgoing' : 'incoming'}`}>
                    <div style={{ fontSize: 11, color: m.from === 'me' ? 'rgba(255,255,255,0.7)' : 'var(--text-tertiary)', marginBottom: 4, display: 'flex', justifyContent: 'space-between' }}>
                      <span>{m.from === 'me' ? '李明辉' : activeConv.name} · {m.time}</span>
                      {m.emotion && <EmotionTag level={m.emotion} />}
                      {m.isInterview && <Tag color="green" style={{ fontSize: 10, padding: '0 6px' }}>疑似面试邀约</Tag>}
                    </div>
                    {m.text}
                  </div>
                </div>
              ))}
            </div>

            {showReplies && activeConv.emotion === 'high' && (
              <div style={{ padding: '0 24px' }}>
                <div className="ai-reply-group">
                  <div className="ai-reply-group__title"><Sparkles size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />AI 建议回复</div>
                  {[
                    { style: '专业正式', text: '感谢您的积极反馈。我们可以安排本周四下午2点进行线上面试，届时会发送会议链接。请问这个时间是否方便？面试预计45分钟，包含技术交流和项目讨论环节。' },
                    { style: '热情友好', text: '太好了，很高兴您对我们的方向感兴趣！这周四或周五下午都可以安排一次线上交流，您看哪个时间更方便？我会提前准备好团队介绍和项目demo给您看。' },
                    { style: '简洁高效', text: '可以安排本周四下午2点线上面试，时长约45分钟。请确认时间是否方便，我会发送会议邀请。' },
                  ].map((r, i) => (
                    <div key={i} className="ai-reply-card" onClick={() => handleAIReply(r.text)}>
                      <div className="ai-reply-card__style">{r.style}</div>{r.text}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="message-thread__input">
              <textarea className="message-thread__textarea" value={replyText} onChange={e => setReplyText(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                placeholder="输入回复内容，或点击上方AI建议使用..." rows={2} />
              <Space direction="vertical" size={4}>
                <AIBtn onClick={() => setShowReplies(!showReplies)}>AI回复</AIBtn>
                <Button type="primary" icon={<Send size={14} />} onClick={handleSend}>发送</Button>
              </Space>
            </div>
          </div>
        ) : (
          <div className="empty-state" style={{ flex: 1 }}><div className="empty-state__icon"><MessageSquare size={24} /></div><div className="empty-state__title">选择对话查看</div></div>
        )}
      </div>
    </div>
  );
};

/* --- Recruiter Jobs List (Interactive) --- */
const RecruiterJobs = () => {
  const navigate = useNavigate();
  const { jobs, closeJob, reopenJob } = useContext(AppState);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchText, setSearchText] = useState('');

  const filtered = jobs.filter(j => {
    if (statusFilter !== 'all' && j.status !== statusFilter) return false;
    if (searchText && !j.name.includes(searchText)) return false;
    return true;
  });

  const columns = [
    { title: '岗位名称', dataIndex: 'name', key: 'name', render: (t, r) => (
      <div style={{ cursor: 'pointer' }} onClick={() => navigate('/recruiter/job/create')}>
        <div style={{ fontWeight: 510, color: 'var(--text-primary)' }}>{t}</div>
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{r.city}</div>
      </div>
    )},
    { title: '薪资', dataIndex: 'salary', key: 'salary', render: t => <span style={{ fontWeight: 510, color: 'var(--color-primary)' }}>{t}</span> },
    { title: '状态', dataIndex: 'status', key: 'status', render: s => {
      const m = { online: { l: '在线', c: 'online' }, pending: { l: '审核中', c: 'pending' }, draft: { l: '草稿', c: 'offline' }, closed: { l: '已下架', c: 'offline' } };
      return <StatusBadge status={m[s]?.c || 'offline'} label={m[s]?.l || s} />;
    }},
    { title: '浏览量', dataIndex: 'views', key: 'views', sorter: (a, b) => a.views - b.views, render: v => <span style={{ fontWeight: 510 }}>{v} <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>人</span></span> },
    { title: '留言数', dataIndex: 'msgs', key: 'msgs', sorter: (a, b) => a.msgs - b.msgs },
    { title: '发布时间', dataIndex: 'date', key: 'date', render: t => <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{t}</span> },
    { title: '操作', key: 'action', render: (_, r) => (
      <Space>
        <Button type="link" size="small" onClick={() => navigate('/recruiter/job/create')}>编辑</Button>
        {r.status === 'online' ? (
          <Button type="link" size="small" danger onClick={() => closeJob(r.key)}>下架</Button>
        ) : r.status === 'closed' ? (
          <Button type="link" size="small" style={{ color: 'var(--color-success)' }} onClick={() => reopenJob(r.key)}>重新上线</Button>
        ) : null}
      </Space>
    )},
  ];

  return (
    <div className="fade-in" data-component="RecruiterJobs">
      <div className="content-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div><h2 className="content-header__title">我的岗位</h2><p className="content-header__subtitle">管理已发布的岗位信息，查看数据表现</p></div>
          <Space>
            <Button icon={<Upload size={14} />} size="large" onClick={() => navigate('/recruiter/job/upload')}>批量上传</Button>
            <Button type="primary" icon={<Plus size={14} />} size="large" onClick={() => navigate('/recruiter/job/create')}>发布新岗位</Button>
          </Space>
        </div>
      </div>
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 20 }}>
        <StatCard icon={<Briefcase size={16} />} label="在线岗位" value={jobs.filter(j => j.status === 'online').length} />
        <StatCard icon={<Eye size={16} />} label="总浏览量" value={jobs.reduce((a, j) => a + j.views, 0).toLocaleString()} delta="+156 本周" deltaType="up" color="var(--color-accent)" />
        <StatCard icon={<MessageSquare size={16} />} label="总留言数" value={jobs.reduce((a, j) => a + j.msgs, 0)} delta="+8 本周" deltaType="up" color="var(--color-success)" />
      </div>
      <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
        <Select value={statusFilter} onChange={setStatusFilter} style={{ width: 120 }} options={[
          { label: '全部状态', value: 'all' }, { label: '在线', value: 'online' }, { label: '审核中', value: 'pending' }, { label: '已下架', value: 'closed' },
        ]} />
        <Input.Search placeholder="搜索岗位名称" style={{ width: 240 }} value={searchText} onChange={e => setSearchText(e.target.value)} onSearch={setSearchText} allowClear />
      </div>
      <Card styles={{ body: { padding: 0 } }}>
        <Table columns={columns} dataSource={filtered} pagination={{ pageSize: 10, showSizeChanger: false }} size="middle" rowKey="key" />
      </Card>
    </div>
  );
};

/* --- Recruiter Job Upload (Batch Import) --- */
const mockParsedJobs = [
  { id: 1, name: 'React Native开发工程师', city: '深圳·南山区', salaryMin: '15K', salaryMax: '25K', type: '月薪', education: '本科', experience: '3年', status: 'ready' },
  { id: 2, name: '测试工程师', city: '深圳·福田区', salaryMin: '10K', salaryMax: '18K', type: '月薪', education: '大专', experience: '2年', status: 'ready' },
  { id: 3, name: '项目经理', city: '广州·天河区', salaryMin: '20K', salaryMax: '35K', type: '月薪', education: '本科', experience: '5年', status: 'ready' },
  { id: 4, name: 'Python后端工程师', city: '深圳·南山区', salaryMin: '18K', salaryMax: '30K', type: '月薪', education: '本科', experience: '3年', status: 'warning', warning: '薪资区间偏窄，建议扩大' },
  { id: 5, name: '新媒体运营专员', city: '广州·番禺区', salaryMin: '6K', salaryMax: '10K', type: '月薪', education: '大专', experience: '1年', status: 'ready' },
];

const RecruiterJobUpload = () => {
  const navigate = useNavigate();
  const { setJobs } = useContext(AppState);
  const [uploadFile, setUploadFile] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [parsedJobs, setParsedJobs] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);

  const handleFileUpload = (file) => {
    setUploadFile({ name: file.name, size: (file.size / 1024).toFixed(1) + ' KB' });
    setParsing(true);
    setParsedJobs([]);
    setTimeout(() => {
      setParsedJobs(mockParsedJobs);
      setSelectedRowKeys(mockParsedJobs.map(j => j.id));
      setParsing(false);
      antMessage.success(`AI解析完成，共识别 ${mockParsedJobs.length} 个岗位`);
    }, 2000);
    return false;
  };

  const handleRemoveFile = () => {
    setUploadFile(null);
    setParsedJobs([]);
    setSelectedRowKeys([]);
  };

  const handleRemoveJob = (id) => {
    setParsedJobs(prev => prev.filter(j => j.id !== id));
    setSelectedRowKeys(prev => prev.filter(k => k !== id));
  };

  const handleSubmitBatch = () => {
    const toSubmit = parsedJobs.filter(j => selectedRowKeys.includes(j.id));
    if (toSubmit.length === 0) { antMessage.warning('请至少选择一个岗位'); return; }
    setSubmitting(true);
    setTimeout(() => {
      const newJobs = toSubmit.map(j => ({
        key: Date.now() + j.id, name: j.name, city: j.city,
        salary: `${j.salaryMin}-${j.salaryMax}`, status: 'pending',
        views: 0, msgs: 0, date: new Date().toISOString().split('T')[0]
      }));
      setJobs(prev => [...newJobs, ...prev]);
      notification.success({ message: `成功提交 ${toSubmit.length} 个岗位`, description: '所有岗位已进入审核流程，预计24小时内完成审核', placement: 'topRight' });
      setSubmitting(false);
      navigate('/recruiter/jobs');
    }, 1500);
  };

  const handleDownloadTemplate = () => {
    antMessage.success('模板下载中...');
  };

  const columns = [
    { title: '岗位名称', dataIndex: 'name', key: 'name', render: (t, r) => (
      <div>
        <div style={{ fontWeight: 510 }}>{t}</div>
        {r.warning && <div style={{ fontSize: 11, color: 'var(--color-warning)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 4 }}><AlertTriangle size={10} />{r.warning}</div>}
      </div>
    )},
    { title: '工作城市', dataIndex: 'city', key: 'city', render: t => <span style={{ fontSize: 13 }}>{t}</span> },
    { title: '薪资', key: 'salary', render: (_, r) => <span style={{ fontWeight: 510, color: 'var(--color-primary)' }}>{r.salaryMin}-{r.salaryMax}</span> },
    { title: '学历', dataIndex: 'education', key: 'education', render: t => <Tag>{t}</Tag> },
    { title: '经验', dataIndex: 'experience', key: 'experience' },
    { title: 'AI校验', dataIndex: 'status', key: 'status', render: s => s === 'ready'
      ? <span style={{ color: 'var(--color-success)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}><CheckCircle2 size={12} />通过</span>
      : <span style={{ color: 'var(--color-warning)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}><AlertTriangle size={12} />建议优化</span>
    },
    { title: '操作', key: 'action', render: (_, r) => (
      <Space>
        <Button type="link" size="small" onClick={() => antMessage.info('编辑功能：可跳转至单条编辑')}>编辑</Button>
        <Button type="link" size="small" danger icon={<Trash2 size={12} />} onClick={() => handleRemoveJob(r.id)}>移除</Button>
      </Space>
    )},
  ];

  return (
    <div className="fade-in" data-component="RecruiterJobUpload">
      <div className="content-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 className="content-header__title">批量上传岗位</h2>
            <p className="content-header__subtitle">通过Excel文件批量导入岗位信息，AI自动解析和校验</p>
          </div>
          <Button icon={<Download size={14} />} onClick={handleDownloadTemplate}>下载模板文件</Button>
        </div>
      </div>

      {!uploadFile && !parsing && parsedJobs.length === 0 && (
        <div style={{ maxWidth: 680 }}>
          <div className="form-section" data-component="UploadZone">
            <div className="form-section__title"><FileSpreadsheet size={18} color="var(--color-primary)" /> 上传岗位文件</div>
            <AntUpload.Dragger
              multiple={false}
              accept=".xlsx,.xls,.csv"
              showUploadList={false}
              beforeUpload={handleFileUpload}
              style={{ padding: '40px 20px' }}
            >
              <p style={{ fontSize: 48, color: 'var(--text-tertiary)', marginBottom: 12 }}><FileSpreadsheet size={48} /></p>
              <p style={{ fontSize: 16, fontWeight: 510, color: 'var(--text-primary)' }}>点击或拖拽Excel文件到此区域</p>
              <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 8 }}>支持 .xlsx、.xls、.csv 格式，单次最多导入50个岗位</p>
              <div style={{ marginTop: 16, display: 'flex', justifyContent: 'center', gap: 24, fontSize: 12, color: 'var(--text-tertiary)' }}>
                <span>每行一个岗位</span>
                <span>必填：岗位名称、城市、薪资</span>
                <span>选填：学历、经验、职责</span>
              </div>
            </AntUpload.Dragger>
          </div>

          <div style={{ marginTop: 20, display: 'flex', gap: 12 }}>
            <div style={{ flex: 1, padding: '16px 20px', background: 'var(--color-accent-soft)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(124,92,252,0.12)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 510, color: 'var(--color-accent)', marginBottom: 6 }}>
                <Sparkles size={14} />AI 智能解析
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>上传后AI将自动识别岗位信息、补全缺失字段、标准化职位名称，并对每个岗位进行合规性校验。</p>
            </div>
            <div style={{ flex: 1, padding: '16px 20px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 510, marginBottom: 6 }}>
                <FileText size={14} color="var(--text-secondary)" />模板格式说明
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>Excel模板需包含以下列：岗位名称（必填）、工作城市（必填）、最低薪资（必填）、最高薪资（必填）、学历要求、经验要求、工作职责。</p>
            </div>
          </div>

          <div style={{ marginTop: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <Activity size={16} color="var(--text-tertiary)" />
              <h4 style={{ margin: 0, fontWeight: 510, fontSize: 14 }}>最近上传记录</h4>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                { file: '2026年5月招聘需求汇总.xlsx', count: 8, time: '2026-05-28 14:30', status: 'success' },
                { file: 'Q2岗位清单_v2.csv', count: 12, time: '2026-05-15 09:20', status: 'success' },
              ].map((record, i) => (
                <div key={i} style={{ padding: '12px 16px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <FileSpreadsheet size={18} color="var(--color-primary)" />
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 510 }}>{record.file}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{record.count} 个岗位 · {record.time}</div>
                    </div>
                  </div>
                  <Tag color="success">已导入</Tag>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {parsing && (
        <div style={{ maxWidth: 680, textAlign: 'center', padding: '60px 20px' }}>
          <div className="ai-review-panel" style={{ background: 'var(--color-accent-soft)', borderColor: 'rgba(124,92,252,0.15)', maxWidth: 400, margin: '0 auto' }}>
            <div style={{ fontSize: 40, marginBottom: 16 }}><Sparkles size={40} color="var(--color-accent)" /></div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 8 }}>
              <Loader2 size={18} className="ai-loading" color="var(--color-accent)" />
              <span style={{ fontSize: 16, fontWeight: 590, color: 'var(--color-accent)' }}>AI 正在解析文件</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>正在识别岗位名称、薪资、城市等信息<br/>自动标准化并校验合规性...</p>
            <Progress percent={68} showInfo={false} strokeColor="var(--color-accent)" style={{ maxWidth: 280, margin: '16px auto 0' }} />
          </div>
        </div>
      )}

      {parsedJobs.length > 0 && !parsing && (
        <div data-component="ParsedJobsPreview">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <div style={{ padding: '8px 16px', background: 'var(--color-success-soft)', borderRadius: 'var(--radius-full)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <CheckCircle2 size={14} color="var(--color-success)" />
              <span style={{ fontSize: 13, fontWeight: 510, color: 'var(--color-success)' }}>解析完成：{parsedJobs.length} 个岗位</span>
            </div>
            <div style={{ padding: '8px 16px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-full)', fontSize: 13 }}>
              文件：{uploadFile?.name}（{uploadFile?.size}）
            </div>
            <Button type="link" size="small" icon={<Upload size={13} />} onClick={() => { handleRemoveFile(); }}>重新上传</Button>
          </div>

          <div className="ai-suggestion-bar" style={{ marginBottom: 16 }}>
            <Sparkles size={16} color="var(--color-accent)" />
            <span className="ai-suggestion-bar__text">AI 已自动校验 {parsedJobs.length} 个岗位，{parsedJobs.filter(j => j.status === 'warning').length} 个有优化建议</span>
            <AIBadge>AI校验</AIBadge>
          </div>

          <Card styles={{ body: { padding: 0 } }}>
            <Table
              columns={columns}
              dataSource={parsedJobs}
              rowKey="id"
              pagination={false}
              size="middle"
              rowSelection={{
                selectedRowKeys,
                onChange: setSelectedRowKeys,
              }}
              footer={() => (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                    已选择 <strong style={{ color: 'var(--color-primary)' }}>{selectedRowKeys.length}</strong> / {parsedJobs.length} 个岗位
                  </span>
                  <Space>
                    <Button onClick={() => { handleRemoveFile(); }}>取消</Button>
                    <Button type="primary" icon={<Send size={14} />} onClick={handleSubmitBatch} loading={submitting}
                      disabled={selectedRowKeys.length === 0}>
                      批量提交审核（{selectedRowKeys.length}）
                    </Button>
                  </Space>
                </div>
              )}
            />
          </Card>

          <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Sparkles size={13} color="var(--color-accent)" />
            提交后岗位将进入AI内容审核 + 人工审核流程，预计24小时内完成。审核通过的岗位自动上线并开始接收应聘者留言。
          </div>
        </div>
      )}
    </div>
  );
};

/* ============================================================
   SEEKER PAGES (with interactions)
   ============================================================ */
const jobListings = [
  { id: 1, title: '高级前端开发工程师', company: '深圳锐智科技（星辰互联）', city: '深圳·南山区', salary: '18K-28K', tags: ['React', 'TypeScript', 'SaaS'], summary: '双休+五险一金的B端SaaS产品团队，技术栈前沿', match: 92, views: 328, responsibility: '1. 负责核心产品前端架构设计与开发\n2. 主导前端技术选型和规范制定\n3. 与产品、设计团队协作，高质量交付需求\n4. 优化性能，提升用户体验\n5. 指导和培养初级工程师', requirement: '1. 本科及以上学历，计算机相关专业\n2. 3年以上React开发经验\n3. 精通TypeScript\n4. 有良好的架构设计能力' },
  { id: 2, title: 'Java后端开发工程师', company: '广州云创数据', city: '广州·天河区', salary: '20K-35K', tags: ['Spring Boot', '微服务', '大数据'], summary: '月入2万+的云计算头部企业核心技术岗', match: 85, views: 256, responsibility: '1. 负责后端核心模块的设计与开发\n2. 参与微服务架构设计与优化\n3. 负责高并发场景的性能调优', requirement: '1. 本科及以上学历\n2. 3年以上Java开发经验\n3. 熟悉Spring Boot、MySQL、Redis' },
  { id: 3, title: 'UI/UX设计师', company: '杭州灵感设计科技', city: '杭州·西湖区', salary: '12K-20K', tags: ['Figma', 'B端设计', '设计系统'], summary: '注重设计文化的创新团队，远程友好', match: 78, views: 189, responsibility: '1. 负责B端产品的界面和交互设计\n2. 参与设计系统的建设和维护\n3. 与产品和开发紧密协作', requirement: '1. 2年以上B端设计经验\n2. 精通Figma\n3. 有设计系统经验优先' },
  { id: 4, title: '产品经理', company: '上海智联未来', city: '上海·浦东新区', salary: '22K-38K', tags: ['B端产品', 'AI方向', '0-1'], summary: 'AI+教育赛道，从0到1打造智能学习平台', match: 71, views: 412, responsibility: '1. 负责AI教育产品的规划和设计\n2. 进行用户调研和需求分析\n3. 推动产品从0到1落地', requirement: '1. 3年以上B端产品经验\n2. 有AI产品经验优先\n3. 优秀的逻辑分析能力' },
  { id: 5, title: '数据分析师', company: '北京数洞科技', city: '北京·海淀区', salary: '15K-25K', tags: ['Python', 'SQL', 'BI'], summary: '数据驱动决策的互联网团队，成长空间大', match: 68, views: 167, responsibility: '1. 负责业务数据分析和建模\n2. 构建数据看板和报表\n3. 提供数据驱动的业务建议', requirement: '1. 熟悉Python和SQL\n2. 有BI工具使用经验\n3. 统计学或数学背景优先' },
];

const SeekerHome = () => {
  const navigate = useNavigate();
  const { favorites, toggleFavorite } = useContext(AppState);
  const [searchText, setSearchText] = useState('');
  const filtered = searchText ? jobListings.filter(j => j.title.includes(searchText) || j.tags.some(t => t.includes(searchText))) : jobListings;

  return (
    <div className="fade-in" data-component="SeekerHome">
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <div className="content-header" style={{ textAlign: 'center', marginBottom: 32 }}>
          <h2 style={{ fontSize: 28, fontWeight: 590, letterSpacing: '-0.02em' }}>发现适合你的机会</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: 8 }}>AI为你精准匹配，每一条推荐都有理由</p>
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          <Input size="large" placeholder="搜索岗位名称、关键词..." prefix={<Search size={16} color="var(--text-tertiary)" />}
            value={searchText} onChange={e => setSearchText(e.target.value)} allowClear style={{ flex: 1 }} />
          <Select size="large" placeholder="城市" defaultValue="all" style={{ width: 120 }} options={[
            { label: '全部', value: 'all' }, { label: '深圳', value: 'sz' }, { label: '广州', value: 'gz' },
          ]} />
          <Button type="primary" size="large" icon={<Search size={16} />} onClick={() => searchText && antMessage.info(`找到 ${filtered.length} 个结果`)}>搜索</Button>
        </div>
        <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sparkles size={16} color="var(--color-accent)" /><span style={{ fontSize: 14, fontWeight: 510 }}>AI 为你推荐</span><AIBadge>个性化排序</AIBadge>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filtered.map(job => (
            <div key={job.id} className="job-card" data-component="JobCard">
              <div className="job-card__header" onClick={() => navigate(`/seeker/job/${job.id}`)} style={{ cursor: 'pointer' }}>
                <div>
                  <div className="job-card__title">{job.title}</div>
                  <div className="job-card__company">{job.company}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="job-card__salary">{job.salary}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}><MapPin size={11} style={{ verticalAlign: 'middle' }} /> {job.city}</div>
                </div>
              </div>
              <div className="job-card__tags">{job.tags.map((t, i) => <span key={i} className="job-card__tag">{t}</span>)}</div>
              <div className="job-card__ai-summary"><Sparkles size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />AI一句话亮点：{job.summary}</div>
              <div className="job-card__footer">
                <div className="match-score"><span style={{ color: 'var(--color-accent)' }}>匹配度</span>
                  <div className="match-score__bar"><div className="match-score__fill" style={{ width: `${job.match}%`, background: 'var(--color-accent)' }} /></div>
                  <span style={{ color: 'var(--color-accent)' }}>{job.match}%</span>
                </div>
                <Space>
                  <Button size="small" icon={<Bookmark size={13} />}
                    style={favorites.has(job.id) ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)' } : {}}
                    onClick={() => toggleFavorite(job.id)}>{favorites.has(job.id) ? '已收藏' : '收藏'}</Button>
                  <Button size="small" type="primary" onClick={() => navigate(`/seeker/job/${job.id}`)}>查看详情</Button>
                </Space>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/* --- Seeker Job Detail (Interactive: message + upload) --- */
const SeekerJobDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { favorites, toggleFavorite, addSeekerMessage, seekerConvos } = useContext(AppState);
  const job = jobListings.find(j => j.id === parseInt(id)) || jobListings[0];
  const [messageModal, setMessageModal] = useState(false);
  const [resumeModal, setResumeModal] = useState(false);
  const [msgText, setMsgText] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleSendMessage = () => {
    if (!msgText.trim()) return;
    addSeekerMessage(101, msgText);
    setMessageModal(false);
    setMsgText('');
    antMessage.success('留言已发送，招聘者将收到通知');
    navigate('/seeker/messages');
  };

  return (
    <div className="fade-in" data-component="SeekerJobDetail" style={{ maxWidth: 720, margin: '0 auto' }}>
      <div style={{ marginBottom: 12 }}>
        <Button type="text" icon={<ArrowLeft size={16} />} onClick={() => navigate('/seeker')}>返回列表</Button>
      </div>

      <div style={{ background: 'var(--bg-base)', borderRadius: 'var(--radius-lg)', padding: 32, border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-card)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 style={{ fontSize: 24, fontWeight: 590, letterSpacing: '-0.02em' }}>{job.title}</h2>
            <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 4 }}>{job.company} · {job.city}</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 24, fontWeight: 590, color: 'var(--color-primary)' }}>{job.salary}</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>元/月 · 14薪</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, margin: '16px 0' }}>
          {[...job.tags, '双休', '五险一金', '弹性工作'].map((t, i) => <Tag key={i} color={i < job.tags.length ? 'blue' : 'default'}>{t}</Tag>)}
        </div>
        <div className="job-card__ai-summary" style={{ marginBottom: 20 }}>
          <Sparkles size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />AI亮点：{job.summary}
        </div>
        <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 20 }}>
          <h4 style={{ marginBottom: 12, fontWeight: 590 }}>工作职责</h4>
          <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>{job.responsibility}</div>
        </div>
        <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 20, marginTop: 20 }}>
          <h4 style={{ marginBottom: 12, fontWeight: 590 }}>任职要求</h4>
          <div style={{ fontSize: 14, lineHeight: 1.8, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>{job.requirement}</div>
        </div>
        <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 20, marginTop: 20 }}>
          <h4 style={{ marginBottom: 12, fontWeight: 590 }}>招聘者联系信息</h4>
          <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}><p>联系人：李经理（虚拟名）</p><p style={{ marginTop: 4 }}>企业邮箱：hr@ruizhi-tech.com</p></div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginTop: 20, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Button size="large" icon={favorites.has(job.id) ? <Bookmark size={16} /> : <BookmarkPlus size={16} />}
          style={favorites.has(job.id) ? { color: 'var(--color-primary)', borderColor: 'var(--color-primary)' } : {}}
          onClick={() => toggleFavorite(job.id)}>{favorites.has(job.id) ? '已收藏' : '收藏职位'}</Button>
        <Button size="large" type="primary" icon={<Send size={16} />} style={{ minWidth: 160 }} onClick={() => setMessageModal(true)}>留言咨询</Button>
        <Button size="large" icon={<Upload size={16} />} onClick={() => setResumeModal(true)}>上传简历</Button>
      </div>

      <div style={{ background: 'var(--color-accent-soft)', borderRadius: 'var(--radius-md)', padding: '16px 20px', marginTop: 20, border: '1px solid rgba(124,92,252,0.12)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Sparkles size={16} color="var(--color-accent)" /><span style={{ fontSize: 13, fontWeight: 510, color: 'var(--color-accent)' }}>完善能力信息，让招聘者更了解你</span></div>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.6 }}>补充工作经历和技能信息后，简历完整度将从45%提升至85%，获得招聘者关注概率提升3倍。</p>
        <Button size="small" type="primary" style={{ marginTop: 8, background: 'var(--color-accent)', borderColor: 'var(--color-accent)' }} onClick={() => antMessage.info('信息完善功能开发中')}>去完善</Button>
      </div>

      {/* Message Modal */}
      <Modal title="留言咨询" open={messageModal} onCancel={() => setMessageModal(false)} footer={null} width={520}>
        <div style={{ marginBottom: 12, padding: '12px 16px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-sm)', fontSize: 13 }}>
          <strong>{job.title}</strong> · {job.company}
        </div>
        <Input.TextArea rows={5} value={msgText} onChange={e => setMsgText(e.target.value)}
          placeholder="向招聘者介绍自己，表达对该岗位的兴趣...（10-500字）" maxLength={500} showCount />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
          <AIBtn onClick={() => { setMsgText('您好，我对贵公司的' + job.title + '岗位非常感兴趣。我有丰富的相关工作经验，希望能进一步了解团队和项目的详细情况。期待有机会与您深入沟通！'); antMessage.success('AI已生成留言草稿'); }}>AI润色</AIBtn>
          <Space>
            <Button onClick={() => setMessageModal(false)}>取消</Button>
            <Button type="primary" icon={<Send size={14} />} onClick={handleSendMessage} disabled={!msgText.trim() || msgText.length < 10}>发送留言</Button>
          </Space>
        </div>
      </Modal>

      {/* Resume Upload Modal */}
      <Modal title="上传简历" open={resumeModal} onCancel={() => setResumeModal(false)} footer={null} width={520}>
        <div style={{ textAlign: 'center', padding: '24px 0' }}>
          <AntUpload.Dragger
            multiple={false}
            accept=".pdf,.doc,.docx"
            fileList={uploadedFiles}
            beforeUpload={(file) => {
              setUploadedFiles([{ uid: '-1', name: file.name, status: 'done' }]);
              antMessage.success(`${file.name} 上传成功`);
              return false;
            }}
            onRemove={() => { setUploadedFiles([]); }}>
            <p style={{ fontSize: 40, color: 'var(--text-tertiary)', marginBottom: 8 }}><Upload size={40} /></p>
            <p style={{ fontSize: 15, fontWeight: 510 }}>点击或拖拽文件到此区域上传</p>
            <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 4 }}>支持 PDF、DOC、DOCX 格式，文件大小不超过 10MB</p>
          </AntUpload.Dragger>
        </div>
        {uploadedFiles.length > 0 && (
          <div style={{ background: 'var(--color-success-soft)', borderRadius: 'var(--radius-sm)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <CheckCircle2 size={16} color="var(--color-success)" />
            <span style={{ fontSize: 13, color: 'var(--color-success)', fontWeight: 510 }}>简历已上传，招聘者可查看</span>
          </div>
        )}
        <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--color-accent-soft)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(124,92,252,0.12)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 510, color: 'var(--color-accent)' }}>
            <Sparkles size={13} />AI 简历解析
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>上传简历后，AI将自动解析并提取关键信息（学历、工作经历、技能等），填充到您的个人资料中。</p>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16, gap: 8 }}>
          <Button onClick={() => setResumeModal(false)}>关闭</Button>
          <Button type="primary" disabled={uploadedFiles.length === 0} onClick={() => { setResumeModal(false); antMessage.success('简历上传成功！'); }}>确认提交</Button>
        </div>
      </Modal>
    </div>
  );
};

/* --- Seeker Subscriptions (Interactive) --- */
const SeekerSubscriptions = () => {
  const { subscriptions, toggleSubscription, removeSubscription, addSubscription } = useContext(AppState);
  const [nlInput, setNlInput] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parsedResult, setParsedResult] = useState(null);

  const handleParse = () => {
    if (!nlInput.trim()) { antMessage.warning('请先输入求职意向描述'); return; }
    setParsing(true);
    setTimeout(() => {
      const keywords = [];
      if (nlInput.includes('前端') || nlInput.includes('开发')) keywords.push('前端开发');
      if (nlInput.includes('设计')) keywords.push('UI设计');
      if (nlInput.includes('产品')) keywords.push('产品经理');
      if (keywords.length === 0) keywords.push(nlInput.split(/[，、\s]/)[0] || '求职');
      const city = (nlInput.match(/(深圳|广州|上海|北京|杭州|成都)/) || ['深圳'])[0];
      const salaryMatch = nlInput.match(/(\d+)/);
      const salary = salaryMatch ? `≥${salaryMatch[1]}K` : '不限';
      setParsedResult({ keywords, city, salary });
      setParsing(false);
    }, 1200);
  };

  const handleCreateFromParsed = () => {
    if (parsedResult) {
      addSubscription(parsedResult);
      setParsedResult(null);
      setNlInput('');
    }
  };

  return (
    <div className="fade-in" data-component="SeekerSubscriptions" style={{ maxWidth: 680, margin: '0 auto' }}>
      <div className="content-header"><h2 className="content-header__title">我的订阅</h2><p className="content-header__subtitle">设置关键词订阅，匹配岗位第一时间推送给你</p></div>
      <div className="form-section">
        <div className="form-section__title"><Sparkles size={18} color="var(--color-accent)" />一句话创建订阅 <AIBadge>AI解析</AIBadge></div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Input size="large" value={nlInput} onChange={e => setNlInput(e.target.value)} placeholder="例如：我想找深圳月薪过万的前端开发工作"
            onPressEnter={handleParse} />
          <Button type="primary" size="large" icon={parsing ? <Loader2 size={14} className="ai-loading" /> : <Sparkles size={14} />}
            onClick={handleParse} loading={parsing} style={{ background: 'var(--color-accent)', borderColor: 'var(--color-accent)' }}>AI解析</Button>
        </div>
        {parsedResult && (
          <div style={{ marginTop: 12, padding: '12px 16px', background: 'var(--color-accent-soft)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: 12, fontWeight: 510, color: 'var(--color-accent)', marginBottom: 6 }}>AI解析结果：</div>
            <div style={{ display: 'flex', gap: 8 }}>
              {parsedResult.keywords.map((k, i) => <Tag key={i} color="purple">{k}</Tag>)}
              <Tag color="blue">{parsedResult.city}</Tag>
              <Tag color="green">{parsedResult.salary}</Tag>
            </div>
            <Button type="primary" size="small" style={{ marginTop: 10, background: 'var(--color-accent)', borderColor: 'var(--color-accent)' }} onClick={handleCreateFromParsed}>创建此订阅</Button>
          </div>
        )}
      </div>

      <div style={{ marginTop: 24 }}>
        <h4 style={{ marginBottom: 12, fontWeight: 510 }}>已有订阅（{subscriptions.length}/10）</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {subscriptions.map(sub => (
            <div key={sub.id} className="sub-card">
              <div style={{ flex: 1 }}>
                <div className="sub-card__keywords">{sub.keywords.map((k, j) => <Tag key={j}>{k}</Tag>)}</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 6, display: 'flex', gap: 16 }}>
                  <span><MapPin size={11} style={{ verticalAlign: 'middle' }} /> {sub.city}</span><span>{sub.salary}</span>
                </div>
              </div>
              <Switch size="small" checked={sub.active} onChange={() => toggleSubscription(sub.id)} />
              <Button type="text" size="small" danger icon={<X size={14} />} onClick={() => removeSubscription(sub.id)} />
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}><Sparkles size={16} color="var(--color-accent)" /><h4 style={{ margin: 0, fontWeight: 510 }}>AI 推荐订阅</h4><AIBadge variant="outline">基于你的背景</AIBadge></div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[
            { keywords: ['TypeScript', '全栈'], city: '深圳', salary: '18K+', reason: '根据你的React经验推荐' },
            { keywords: ['远程办公', '前端'], city: '不限', salary: '15K+', reason: '近期远程岗位增长35%' },
          ].map((rec, i) => (
            <div key={i} style={{ padding: '12px 16px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', border: '1px dashed rgba(124,92,252,0.2)', display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {rec.keywords.map((k, j) => <Tag key={j} color="purple" style={{ fontSize: 11 }}>{k}</Tag>)}
                  <Tag style={{ fontSize: 11 }}>{rec.city}</Tag><Tag style={{ fontSize: 11 }}>{rec.salary}</Tag>
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-accent)', marginTop: 4 }}>{rec.reason}</div>
              </div>
              <Button size="small" style={{ background: 'var(--color-accent-soft)', color: 'var(--color-accent)', borderColor: 'rgba(124,92,252,0.3)' }}
                onClick={() => { addSubscription(rec); antMessage.success('已添加推荐订阅'); }}>一键订阅</Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/* --- Seeker Messages (Interactive) --- */
const SeekerMessages = () => {
  const { seekerConvos, addSeekerMessage } = useContext(AppState);
  const [activeTab, setActiveTab] = useState('conversations');
  const [activeId, setActiveId] = useState(null);
  const [replyText, setReplyText] = useState('');
  const activeConv = seekerConvos.find(c => c.id === activeId);

  const handleSend = () => {
    if (!replyText.trim() || !activeId) return;
    addSeekerMessage(activeId, replyText);
    setReplyText('');
    antMessage.success('回复已发送');
  };

  return (
    <div className="fade-in" data-component="SeekerMessages" style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="content-header"><h2 className="content-header__title">消息中心</h2><p className="content-header__subtitle">查看招聘者回复和平台推送</p></div>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'conversations', label: <span>对话 <Badge count={seekerConvos.reduce((a, c) => a + c.unread, 0)} style={{ marginLeft: 4 }} /></span>,
          children: activeId && activeConv ? (
            <div style={{ background: 'var(--bg-base)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Button type="text" size="small" icon={<ArrowLeft size={14} />} onClick={() => setActiveId(null)}>返回</Button>
                <span style={{ fontWeight: 590 }}>{activeConv.name}</span>
                {activeConv.isInterview && <Tag color="green" style={{ fontSize: 10 }}>疑似面试邀约</Tag>}
              </div>
              <div style={{ padding: 16, maxHeight: 320, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {activeConv.messages.map((m, i) => (
                  <div key={i} className={`message-bubble message-bubble--${m.from === 'me' ? 'outgoing' : 'incoming'}`}>
                    <div style={{ fontSize: 11, color: m.from === 'me' ? 'rgba(255,255,255,0.7)' : 'var(--text-tertiary)', marginBottom: 4 }}>
                      {m.from === 'me' ? '我' : activeConv.name} · {m.time}
                      {m.isInterview && <Tag color="green" style={{ fontSize: 10, marginLeft: 6 }}>疑似面试邀约</Tag>}
                    </div>{m.text}
                  </div>
                ))}
              </div>
              {activeConv.isInterview && (
                <div style={{ padding: '8px 16px', background: 'var(--color-success-soft)', display: 'flex', gap: 8 }}>
                  <Button size="small" type="primary" onClick={() => { antMessage.success('已确认面试时间'); }}>确认面试</Button>
                  <Button size="small" onClick={() => { antMessage.info('已发送改期请求'); }}>请求改期</Button>
                </div>
              )}
              <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border-light)', display: 'flex', gap: 8 }}>
                <Input value={replyText} onChange={e => setReplyText(e.target.value)} placeholder="输入回复..." onPressEnter={handleSend} />
                <Button type="primary" icon={<Send size={14} />} onClick={handleSend}>发送</Button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {seekerConvos.map(c => (
                <div key={c.id} className="job-card" style={{ padding: '16px 20px', cursor: 'pointer' }} onClick={() => setActiveId(c.id)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontWeight: 510, display: 'flex', alignItems: 'center', gap: 8 }}>{c.name}
                        {c.isInterview && <Tag color="green" style={{ fontSize: 10 }}>疑似面试邀约</Tag>}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>{c.job}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{c.time}</span>
                      {c.unread > 0 && <Badge count={c.unread} />}
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>{c.preview}</div>
                </div>
              ))}
            </div>
          )
        },
        { key: 'push', label: <span>推送通知 <Badge count={5} style={{ marginLeft: 4 }} /></span>,
          children: (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 4 }}>今日 · 2026年6月2日</div>
              {jobListings.slice(0, 3).map(job => (
                <div key={job.id} className="job-card" style={{ padding: '14px 18px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div style={{ fontWeight: 510 }}>{job.title}</div>
                    <div style={{ fontWeight: 590, color: 'var(--color-primary)', fontSize: 15 }}>{job.salary}</div>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>{job.company} · {job.city}</div>
                  <div className="job-card__ai-summary" style={{ marginTop: 8, marginBottom: 0 }}><Sparkles size={10} style={{ verticalAlign: 'middle', marginRight: 4 }} />{job.summary}</div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
                    <Button size="small" type="primary">查看详情</Button>
                  </div>
                </div>
              ))}
            </div>
          )
        },
      ]} />
    </div>
  );
};

/* ============================================================
   ADMIN PAGES (with interactions)
   ============================================================ */
const adminDashboardData = [
  { day: '5/27', newJobs: 12, newUsers: 85, interactions: 120 },
  { day: '5/28', newJobs: 18, newUsers: 102, interactions: 156 },
  { day: '5/29', newJobs: 15, newUsers: 93, interactions: 178 },
  { day: '5/30', newJobs: 22, newUsers: 128, interactions: 210 },
  { day: '5/31', newJobs: 19, newUsers: 115, interactions: 195 },
  { day: '6/1', newJobs: 25, newUsers: 142, interactions: 238 },
  { day: '6/2', newJobs: 16, newUsers: 98, interactions: 165 },
];

const AdminDashboard = () => {
  const navigate = useNavigate();
  return (
  <div className="fade-in" data-component="AdminDashboard">
    <div className="content-header"><h2 className="content-header__title">平台数据看板</h2><p className="content-header__subtitle">实时监控平台运营指标和AI效能数据</p></div>
    <div className="stats-grid">
      <StatCard icon={<Users size={16} />} label="今日活跃用户(DAU)" value="1,286" delta="+8.3% vs 昨日" deltaType="up" onClick={() => navigate('/admin/users')} />
      <StatCard icon={<Briefcase size={16} />} label="本月新增岗位" value="387" delta="+12.5% vs 上月" deltaType="up" color="var(--color-accent)" />
      <StatCard icon={<UserCircle size={16} />} label="本月新注册" value="1,063" delta="+15.2% vs 上月" deltaType="up" color="var(--color-success)" onClick={() => navigate('/admin/users')} />
      <StatCard icon={<MessageSquare size={16} />} label="今日互动量" value="165" delta="-3.2% vs 昨日" deltaType="down" color="var(--color-warning)" />
    </div>
    <div className="grid-2" style={{ marginBottom: 24 }}>
      <div className="chart-card">
        <div className="chart-card__title">平台核心指标趋势（近7日）</div>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={adminDashboardData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
            <XAxis dataKey="day" tick={{ fontSize: 12, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} />
            <ReTooltip contentStyle={{ borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13 }} />
            <Line type="monotone" dataKey="newJobs" stroke="var(--color-primary)" strokeWidth={2} dot={{ r: 3 }} name="新增岗位" />
            <Line type="monotone" dataKey="newUsers" stroke="var(--color-success)" strokeWidth={2} dot={{ r: 3 }} name="新注册用户" />
            <Line type="monotone" dataKey="interactions" stroke="var(--color-accent)" strokeWidth={2} dot={{ r: 3 }} name="互动量" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="insight-card">
        <div className="insight-card__header"><Sparkles size={18} color="var(--color-accent)" /><h4 style={{ margin: 0 }}>AI 效能看板</h4></div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 8 }}>
          {[
            { label: 'AI功能日调用量', value: '2,340', sub: '次/日', color: 'var(--color-accent)' },
            { label: 'AI建议采纳率', value: '42.8%', sub: '+5.2% vs 上周', color: 'var(--color-success)' },
            { label: 'AI内容审核自动通过率', value: '67.3%', sub: '目标≥60% ✓', color: 'var(--color-primary)' },
            { label: 'AI客服解决率', value: '58.2%', sub: '目标≥50% ✓', color: 'var(--color-warning)' },
          ].map((m, i) => (
            <div key={i} style={{ padding: '12px 16px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 4 }}>{m.label}</div>
              <div style={{ fontSize: 22, fontWeight: 590, color: m.color, letterSpacing: '-0.02em' }}>{m.value}</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{m.sub}</div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--color-accent-soft)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(124,92,252,0.12)' }}>
          <div style={{ fontSize: 12, fontWeight: 510, color: 'var(--color-accent)', marginBottom: 6 }}>AI服务健康状态</div>
          <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-success)', display: 'inline-block' }} />LLM服务正常</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-success)', display: 'inline-block' }} />OCR服务正常</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-success)', display: 'inline-block' }} />内容审核正常</span>
          </div>
        </div>
      </div>
    </div>
    <div className="grid-2">
      <div className="chart-card">
        <div className="chart-card__title">内容质量指标</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 8 }}>
          {[
            { label: '企业认证通过率', value: 82, target: '目标≥80%' },
            { label: '岗位审核通过率', value: 91, target: '目标≥85%' },
            { label: 'JD模板使用率', value: 38, target: '目标≥30%' },
            { label: '信息完整度≥60%用户占比', value: 72, target: '目标≥65%' },
          ].map((m, i) => (
            <div key={i}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 13, fontWeight: 450 }}>{m.label}</span>
                <span style={{ fontSize: 13, fontWeight: 590, color: m.value >= parseInt(m.target.split('≥')[1]) ? 'var(--color-success)' : 'var(--color-warning)' }}>{m.value}%</span>
              </div>
              <Progress percent={m.value} showInfo={false} strokeColor={m.value >= parseInt(m.target.split('≥')[1]) ? 'var(--color-success)' : 'var(--color-warning)'} size="small" />
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{m.target}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="insight-card">
        <div className="insight-card__header"><AlertTriangle size={18} color="var(--color-warning)" /><h4 style={{ margin: 0 }}>近期异常告警</h4></div>
        {[
          { type: 'warning', icon: <Shield size={16} />, title: '疑似假冒企业注册', desc: '检测到"XX金融集团"注册信息异常，已标记高风险', time: '1小时前' },
          { type: 'error', icon: <XCircle size={16} />, title: 'AI内容审核拦截', desc: '岗位"高薪诚聘"包含虚假薪资信息，已自动拦截', time: '3小时前' },
          { type: 'warning', icon: <Activity size={16} />, title: '推送服务延迟', desc: '微信模板消息推送延迟率升至5.2%，已触发告警', time: '今天 08:30' },
        ].map((alert, i) => (
          <div className="todo-item" key={i}>
            <div className="todo-item__icon" style={{ background: alert.type === 'error' ? 'var(--color-error-soft)' : 'var(--color-warning-soft)', color: alert.type === 'error' ? 'var(--color-error)' : 'var(--color-warning)' }}>{alert.icon}</div>
            <div className="todo-item__content"><div className="todo-item__title">{alert.title}</div><div className="todo-item__desc">{alert.desc}</div></div>
            <span className="todo-item__time">{alert.time}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
  );
};

/* --- Admin Review (Interactive) --- */
const AdminReview = () => {
  const { reviewItems, approveReview, rejectReview } = useContext(AppState);
  const [activeTab, setActiveTab] = useState('all');
  const statusMap = {
    pending: { label: '待审核', color: 'var(--color-warning)', bg: 'var(--color-warning-soft)' },
    warning: { label: 'AI警告', color: 'var(--color-warning)', bg: 'var(--color-warning-soft)' },
    blocked: { label: 'AI拦截', color: 'var(--color-error)', bg: 'var(--color-error-soft)' },
  };
  const filtered = activeTab === 'all' ? reviewItems :
    activeTab === 'enterprise' ? reviewItems.filter(r => r.type === '企业资质') :
    activeTab === 'job' ? reviewItems.filter(r => r.type === '岗位内容') :
    reviewItems.filter(r => r.status === 'blocked');

  return (
    <div className="fade-in" data-component="AdminReview">
      <div className="content-header"><h2 className="content-header__title">审核管理</h2><p className="content-header__subtitle">AI辅助审核，高效处理企业资质和岗位内容审核</p></div>
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 20 }}>
        <StatCard icon={<Clock size={16} />} label="待审核" value={reviewItems.filter(r => r.status === 'pending').length} color="var(--color-warning)" />
        <StatCard icon={<CheckCircle2 size={16} />} label="今日已通过" value="23" color="var(--color-success)" />
        <StatCard icon={<XCircle size={16} />} label="今日已拦截" value={reviewItems.filter(r => r.status === 'blocked').length} color="var(--color-error)" />
        <StatCard icon={<Sparkles size={16} />} label="AI自动通过率" value="67.3%" delta="+3.1%" deltaType="up" color="var(--color-accent)" />
      </div>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'all', label: `全部 (${reviewItems.length})` },
        { key: 'enterprise', label: `企业资质 (${reviewItems.filter(r => r.type === '企业资质').length})` },
        { key: 'job', label: `岗位内容 (${reviewItems.filter(r => r.type === '岗位内容').length})` },
        { key: 'risk', label: <span>高风险 <Badge count={reviewItems.filter(r => r.status === 'blocked').length} style={{ backgroundColor: 'var(--color-error)' }} /></span> },
      ]} />
      <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filtered.length === 0 ? (
          <div className="empty-state"><div className="empty-state__icon"><CheckCircle2 size={24} /></div><div className="empty-state__title">暂无待审核项</div></div>
        ) : filtered.map(item => {
          const st = statusMap[item.status];
          return (
            <div key={item.id} style={{ background: 'var(--bg-base)', borderRadius: 'var(--radius-lg)', padding: '20px 24px', border: `1px solid ${item.status === 'blocked' ? 'rgba(255,77,79,0.2)' : 'var(--border-light)'}`, boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <Tag color={item.type === '企业资质' ? 'blue' : 'purple'}>{item.type}</Tag>
                    <span style={{ fontSize: 12, fontWeight: 510, padding: '2px 8px', borderRadius: 'var(--radius-full)', color: st.color, background: st.bg }}>{st.label}</span>
                  </div>
                  <div style={{ fontWeight: 510, fontSize: 15, marginTop: 4 }}>{item.company}</div>
                  {item.job && <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>岗位：{item.job}</div>}
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>提交人：{item.submitter} · {item.time}</div>
                </div>
                <Space>
                  <Button type="primary" size="small" icon={<CheckCircle2 size={13} />} onClick={() => approveReview(item.id)}>通过</Button>
                  <Button danger size="small" icon={<XCircle size={13} />} onClick={() => rejectReview(item.id)}>不通过</Button>
                </Space>
              </div>
              <div style={{ marginTop: 12, padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: item.aiResult === 'pass' ? 'var(--color-success-soft)' : item.aiResult === 'warning' ? 'var(--color-warning-soft)' : 'var(--color-error-soft)', border: `1px solid ${item.aiResult === 'pass' ? 'rgba(82,196,26,0.15)' : item.aiResult === 'warning' ? 'rgba(250,173,20,0.15)' : 'rgba(255,77,79,0.15)'}` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 510, color: item.aiResult === 'pass' ? 'var(--color-success)' : item.aiResult === 'warning' ? 'var(--color-warning)' : 'var(--color-error)' }}>
                  <Sparkles size={13} />AI 预审结论 <AIBadge variant="outline">AI辅助</AIBadge>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{item.aiNote}</div>
                <div style={{ marginTop: 6 }}>
                  <Button size="small" type="link" style={{ fontSize: 12, padding: 0 }}
                    onClick={() => { item.aiResult === 'pass' ? approveReview(item.id) : rejectReview(item.id); }}>一键采纳AI建议</Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/* --- Admin User Management (Interactive) --- */
const mockUsers = [
  { id: 1, name: '王晓明', role: 'recruiter', company: '深圳锐智科技有限公司', phone: '138****2341', regDate: '2026-03-15', lastActive: '10分钟前', status: 'active', jobs: 12, verified: true },
  { id: 2, name: '张丽华', role: 'recruiter', company: '广州云创数据科技', phone: '135****8920', regDate: '2026-04-02', lastActive: '1小时前', status: 'active', jobs: 8, verified: true },
  { id: 3, name: '陈思远', role: 'seeker', company: '—', phone: '139****5567', regDate: '2026-05-10', lastActive: '30分钟前', status: 'active', jobs: 0, verified: true },
  { id: 4, name: '刘佳', role: 'seeker', company: '—', phone: '137****3344', regDate: '2026-05-18', lastActive: '2小时前', status: 'active', jobs: 0, verified: false },
  { id: 5, name: '陈某', role: 'recruiter', company: '深圳XX金融集团', phone: '186****7712', regDate: '2026-05-28', lastActive: '3天前', status: 'suspended', jobs: 0, verified: false },
  { id: 6, name: '赵敏', role: 'seeker', company: '—', phone: '158****4421', regDate: '2026-04-22', lastActive: '昨天', status: 'active', jobs: 0, verified: true },
  { id: 7, name: '李芳', role: 'recruiter', company: '杭州灵感设计科技', phone: '136****9908', regDate: '2026-02-20', lastActive: '20分钟前', status: 'active', jobs: 5, verified: true },
  { id: 8, name: '黄伟杰', role: 'seeker', company: '—', phone: '150****6633', regDate: '2026-05-30', lastActive: '5分钟前', status: 'active', jobs: 0, verified: false },
];

const AdminUserManagement = () => {
  const [users, setUsers] = useState(mockUsers);
  const [activeTab, setActiveTab] = useState('all');
  const [searchText, setSearchText] = useState('');
  const [detailUser, setDetailUser] = useState(null);

  const filtered = users.filter(u => {
    if (activeTab === 'recruiter' && u.role !== 'recruiter') return false;
    if (activeTab === 'seeker' && u.role !== 'seeker') return false;
    if (activeTab === 'risk' && u.status !== 'suspended') return false;
    if (searchText && !u.name.includes(searchText) && !u.company.includes(searchText) && !u.phone.includes(searchText)) return false;
    return true;
  });

  const toggleStatus = (id) => {
    setUsers(prev => prev.map(u => {
      if (u.id !== id) return u;
      const next = u.status === 'active' ? 'suspended' : 'active';
      antMessage.success(`${u.name} 已${next === 'active' ? '恢复' : '停用'}`);
      return { ...u, status: next };
    }));
  };

  const handleResetPassword = (name) => {
    Modal.confirm({
      title: `重置 ${name} 的密码？`,
      content: '重置后将通过短信发送新密码到用户注册手机号',
      okText: '确认重置',
      cancelText: '取消',
      onOk: () => antMessage.success(`已向 ${name} 发送密码重置短信`),
    });
  };

  return (
    <div className="fade-in" data-component="AdminUserManagement">
      <div className="content-header">
        <h2 className="content-header__title">用户管理</h2>
        <p className="content-header__subtitle">管理平台注册企业和个人用户，查看用户详情与行为数据</p>
      </div>
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 20 }}>
        <StatCard icon={<Users size={16} />} label="总注册用户" value={users.length.toLocaleString()} delta="+28 本周" deltaType="up" />
        <StatCard icon={<Building2 size={16} />} label="认证企业" value={users.filter(u => u.role === 'recruiter' && u.verified).length} color="var(--color-primary)" />
        <StatCard icon={<UserCircle size={16} />} label="活跃求职者" value={users.filter(u => u.role === 'seeker' && u.status === 'active').length} color="var(--color-success)" />
        <StatCard icon={<AlertTriangle size={16} />} label="已停用" value={users.filter(u => u.status === 'suspended').length} color="var(--color-error)" />
      </div>
      <div style={{ marginBottom: 12, display: 'flex', gap: 8 }}>
        <Input.Search placeholder="搜索用户名、企业名、手机号" style={{ width: 320 }} value={searchText} onChange={e => setSearchText(e.target.value)} onSearch={setSearchText} allowClear />
        <Button icon={<Download size={14} />} onClick={() => antMessage.success('用户数据导出中...')}>导出</Button>
      </div>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'all', label: `全部 (${users.length})` },
        { key: 'recruiter', label: `招聘者 (${users.filter(u => u.role === 'recruiter').length})` },
        { key: 'seeker', label: `求职者 (${users.filter(u => u.role === 'seeker').length})` },
        { key: 'risk', label: <span>异常用户 <Badge count={users.filter(u => u.status === 'suspended').length} style={{ backgroundColor: 'var(--color-error)' }} /></span> },
      ]} />
      <Card styles={{ body: { padding: 0 } }} style={{ marginTop: 8 }}>
        <Table dataSource={filtered} pagination={{ pageSize: 8, showSizeChanger: false }} size="middle" rowKey="id"
          columns={[
            { title: '用户', dataIndex: 'name', key: 'name', render: (t, r) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Avatar size={32} style={{ background: r.role === 'recruiter' ? 'var(--color-primary)' : 'var(--color-success)', fontSize: 13 }}>{t[0]}</Avatar>
                <div>
                  <div style={{ fontWeight: 510, display: 'flex', alignItems: 'center', gap: 6 }}>{t}{r.verified && <CheckCircle2 size={12} color="var(--color-success)" />}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{r.phone}</div>
                </div>
              </div>
            )},
            { title: '角色', dataIndex: 'role', key: 'role', render: r => <Tag color={r === 'recruiter' ? 'blue' : 'green'}>{r === 'recruiter' ? '招聘者' : '求职者'}</Tag> },
            { title: '所属企业', dataIndex: 'company', key: 'company', render: t => <span style={{ fontSize: 13 }}>{t}</span> },
            { title: '注册时间', dataIndex: 'regDate', key: 'regDate', render: t => <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{t}</span> },
            { title: '最近活跃', dataIndex: 'lastActive', key: 'lastActive', render: t => <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{t}</span> },
            { title: '状态', dataIndex: 'status', key: 'status', render: s => <StatusBadge status={s === 'active' ? 'online' : 'offline'} label={s === 'active' ? '正常' : '已停用'} /> },
            { title: '操作', key: 'action', render: (_, r) => (
              <Space>
                <Button type="link" size="small" onClick={() => setDetailUser(r)}>详情</Button>
                <Button type="link" size="small" style={{ color: r.status === 'active' ? 'var(--color-error)' : 'var(--color-success)' }}
                  onClick={() => toggleStatus(r.id)}>{r.status === 'active' ? '停用' : '恢复'}</Button>
                <Button type="link" size="small" onClick={() => handleResetPassword(r.name)}>重置密码</Button>
              </Space>
            )},
          ]}
        />
      </Card>

      <Drawer title="用户详情" open={!!detailUser} onClose={() => setDetailUser(null)} width={480}>
        {detailUser && (
          <div data-component="UserDetailDrawer">
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Avatar size={64} style={{ background: detailUser.role === 'recruiter' ? 'var(--color-primary)' : 'var(--color-success)', fontSize: 24 }}>{detailUser.name[0]}</Avatar>
              <h3 style={{ margin: '12px 0 4px', fontWeight: 590 }}>{detailUser.name}</h3>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 8 }}>
                <Tag color={detailUser.role === 'recruiter' ? 'blue' : 'green'}>{detailUser.role === 'recruiter' ? '招聘者' : '求职者'}</Tag>
                <StatusBadge status={detailUser.status === 'active' ? 'online' : 'offline'} label={detailUser.status === 'active' ? '正常' : '已停用'} />
                {detailUser.verified && <Tag color="success">已认证</Tag>}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ padding: '16px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 8, fontWeight: 510 }}>基本信息</div>
                {[
                  { label: '手机号', value: detailUser.phone },
                  { label: '所属企业', value: detailUser.company },
                  { label: '注册时间', value: detailUser.regDate },
                  { label: '最近活跃', value: detailUser.lastActive },
                ].map((item, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: 13 }}>
                    <span style={{ color: 'var(--text-tertiary)' }}>{item.label}</span><span style={{ fontWeight: 510 }}>{item.value}</span>
                  </div>
                ))}
              </div>
              {detailUser.role === 'recruiter' && (
                <div style={{ padding: '16px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 8, fontWeight: 510 }}>招聘数据</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div style={{ textAlign: 'center', padding: '12px', background: 'var(--bg-base)', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontSize: 22, fontWeight: 590, color: 'var(--color-primary)' }}>{detailUser.jobs}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>发布岗位</div>
                    </div>
                    <div style={{ textAlign: 'center', padding: '12px', background: 'var(--bg-base)', borderRadius: 'var(--radius-sm)' }}>
                      <div style={{ fontSize: 22, fontWeight: 590, color: 'var(--color-success)' }}>{Math.floor(Math.random() * 200 + 50)}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>收到留言</div>
                    </div>
                  </div>
                </div>
              )}
              <div style={{ padding: '16px', background: 'var(--color-accent-soft)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(124,92,252,0.12)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 510, color: 'var(--color-accent)', marginBottom: 8 }}>
                  <Sparkles size={14} />AI 用户画像
                </div>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0 }}>
                  {detailUser.role === 'recruiter'
                    ? `该招聘者活跃度${detailUser.jobs > 5 ? '高' : '中等'}，发布岗位集中在${detailUser.jobs > 5 ? '技术和设计类' : '基础岗位'}，平均岗位信息完整度85%，消息回复率92%，信用评分良好。`
                    : `该求职者近期活跃，浏览了${Math.floor(Math.random() * 20 + 5)}个岗位，收藏了${Math.floor(Math.random() * 8 + 2)}个，主要关注${['前端开发', 'UI设计', '产品管理'][Math.floor(Math.random() * 3)]}方向，简历完整度${Math.floor(Math.random() * 30 + 60)}%。`}
                </p>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Button type="primary" style={{ flex: 1 }} onClick={() => { antMessage.success('已发送系统通知'); }}>发送通知</Button>
                <Button danger style={{ flex: 1 }} onClick={() => { toggleStatus(detailUser.id); setDetailUser(null); }}>
                  {detailUser.status === 'active' ? '停用账号' : '恢复账号'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

/* --- Admin Base Data (Interactive) --- */
const baseJobTitles = [
  { id: 1, name: '前端开发工程师', category: '技术研发', aliases: ['Web开发', '前端工程师', 'H5开发'], jobCount: 128, status: 'active' },
  { id: 2, name: 'Java开发工程师', category: '技术研发', aliases: ['Java后端', 'Java程序员', '后端开发'], jobCount: 96, status: 'active' },
  { id: 3, name: 'UI/UX设计师', category: '设计', aliases: ['UI设计', '交互设计', '视觉设计'], jobCount: 54, status: 'active' },
  { id: 4, name: '产品经理', category: '产品运营', aliases: ['PM', '产品专员', '产品总监'], jobCount: 72, status: 'active' },
  { id: 5, name: '数据分析师', category: '数据', aliases: ['BI分析', '数据挖掘'], jobCount: 38, status: 'active' },
  { id: 6, name: '销售经理', category: '市场销售', aliases: ['销售代表', '客户经理'], jobCount: 45, status: 'active' },
  { id: 7, name: '运维工程师', category: '技术研发', aliases: ['DevOps', 'SRE', '系统运维'], jobCount: 29, status: 'active' },
  { id: 8, name: '新媒体运营', category: '产品运营', aliases: ['内容运营', '社交媒体运营'], jobCount: 33, status: 'active' },
];

const baseCities = [
  { id: 1, name: '深圳', region: '华南', tier: '一线', jobCount: 456, seekerCount: 2380, status: 'active' },
  { id: 2, name: '广州', region: '华南', tier: '一线', jobCount: 312, seekerCount: 1850, status: 'active' },
  { id: 3, name: '北京', region: '华北', tier: '一线', jobCount: 520, seekerCount: 3100, status: 'active' },
  { id: 4, name: '上海', region: '华东', tier: '一线', jobCount: 488, seekerCount: 2950, status: 'active' },
  { id: 5, name: '杭州', region: '华东', tier: '新一线', jobCount: 268, seekerCount: 1420, status: 'active' },
  { id: 6, name: '成都', region: '西南', tier: '新一线', jobCount: 195, seekerCount: 1080, status: 'active' },
  { id: 7, name: '武汉', region: '华中', tier: '新一线', jobCount: 162, seekerCount: 920, status: 'active' },
  { id: 8, name: '南京', region: '华东', tier: '新一线', jobCount: 148, seekerCount: 850, status: 'active' },
];

const baseSalaryBenchmarks = [
  { id: 1, jobCategory: '前端开发', city: '深圳', p25: '10K', p50: '16K', p75: '25K', p90: '35K', sampleSize: 320, updatedAt: '2026-06-01' },
  { id: 2, jobCategory: 'Java开发', city: '深圳', p25: '12K', p50: '20K', p75: '30K', p90: '42K', sampleSize: 280, updatedAt: '2026-06-01' },
  { id: 3, jobCategory: 'UI设计', city: '深圳', p25: '8K', p50: '13K', p75: '20K', p90: '28K', sampleSize: 156, updatedAt: '2026-05-28' },
  { id: 4, jobCategory: '产品经理', city: '深圳', p25: '15K', p50: '22K', p75: '35K', p90: '50K', sampleSize: 198, updatedAt: '2026-06-01' },
  { id: 5, jobCategory: '数据分析', city: '广州', p25: '10K', p50: '17K', p75: '25K', p90: '35K', sampleSize: 120, updatedAt: '2026-05-28' },
  { id: 6, jobCategory: '销售', city: '广州', p25: '5K', p50: '8K', p75: '15K', p90: '25K', sampleSize: 240, updatedAt: '2026-05-25' },
];

const AdminBaseData = () => {
  const [activeTab, setActiveTab] = useState('jobs');
  const [jobTitles, setJobTitles] = useState(baseJobTitles);
  const [cities] = useState(baseCities);
  const [benchmarks] = useState(baseSalaryBenchmarks);
  const [editModal, setEditModal] = useState(null);
  const [searchText, setSearchText] = useState('');

  const toggleJobTitle = (id) => {
    setJobTitles(prev => prev.map(j => {
      if (j.id !== id) return j;
      const next = j.status === 'active' ? 'disabled' : 'active';
      antMessage.success(`「${j.name}」已${next === 'active' ? '启用' : '停用'}`);
      return { ...j, status: next };
    }));
  };

  const handleSyncSalary = () => {
    antMessage.info('正在从市场数据源同步最新薪资基准...');
    setTimeout(() => antMessage.success('薪资基准数据已更新'), 1500);
  };

  const jobColumns = [
    { title: '标准职位名', dataIndex: 'name', key: 'name', render: (t, r) => (
      <div><div style={{ fontWeight: 510 }}>{t}</div><div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>别名：{r.aliases.join('、')}</div></div>
    )},
    { title: '分类', dataIndex: 'category', key: 'category', render: t => <Tag>{t}</Tag> },
    { title: '关联岗位', dataIndex: 'jobCount', key: 'jobCount', sorter: (a, b) => a.jobCount - b.jobCount, render: v => <span style={{ fontWeight: 510 }}>{v}</span> },
    { title: 'AI标准化', key: 'ai', render: () => <span style={{ color: 'var(--color-accent)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}><Sparkles size={11} />已启用</span> },
    { title: '状态', dataIndex: 'status', key: 'status', render: s => <StatusBadge status={s === 'active' ? 'online' : 'offline'} label={s === 'active' ? '启用' : '停用'} /> },
    { title: '操作', key: 'action', render: (_, r) => (
      <Space>
        <Button type="link" size="small" onClick={() => setEditModal(r)}>编辑</Button>
        <Button type="link" size="small" style={{ color: r.status === 'active' ? 'var(--color-error)' : 'var(--color-success)' }} onClick={() => toggleJobTitle(r.id)}>{r.status === 'active' ? '停用' : '启用'}</Button>
      </Space>
    )},
  ];

  const cityColumns = [
    { title: '城市', dataIndex: 'name', key: 'name', render: t => <span style={{ fontWeight: 510 }}>{t}</span> },
    { title: '区域', dataIndex: 'region', key: 'region' },
    { title: '等级', dataIndex: 'tier', key: 'tier', render: t => <Tag color={t === '一线' ? 'gold' : 'blue'}>{t}</Tag> },
    { title: '在招岗位', dataIndex: 'jobCount', key: 'jobCount', sorter: (a, b) => a.jobCount - b.jobCount, render: v => <span style={{ fontWeight: 510 }}>{v}</span> },
    { title: '注册求职者', dataIndex: 'seekerCount', key: 'seekerCount', sorter: (a, b) => a.seekerCount - b.seekerCount, render: v => <span style={{ fontWeight: 510 }}>{v.toLocaleString()}</span> },
    { title: '供需比', key: 'ratio', render: (_, r) => {
      const ratio = (r.seekerCount / r.jobCount).toFixed(1);
      return <span style={{ fontWeight: 510, color: ratio > 6 ? 'var(--color-success)' : ratio > 4 ? 'var(--color-warning)' : 'var(--color-error)' }}>{ratio}:1</span>;
    }},
    { title: '状态', dataIndex: 'status', key: 'status', render: () => <StatusBadge status="online" label="已开通" /> },
  ];

  const salaryColumns = [
    { title: '职位类别', dataIndex: 'jobCategory', key: 'jobCategory', render: t => <span style={{ fontWeight: 510 }}>{t}</span> },
    { title: '城市', dataIndex: 'city', key: 'city', render: t => <Tag>{t}</Tag> },
    { title: 'P25', dataIndex: 'p25', key: 'p25', render: t => <span style={{ color: 'var(--text-secondary)' }}>{t}</span> },
    { title: 'P50（中位数）', dataIndex: 'p50', key: 'p50', render: t => <span style={{ fontWeight: 590, color: 'var(--color-primary)' }}>{t}</span> },
    { title: 'P75', dataIndex: 'p75', key: 'p75', render: t => <span style={{ color: 'var(--text-secondary)' }}>{t}</span> },
    { title: 'P90', dataIndex: 'p90', key: 'p90', render: t => <span style={{ fontWeight: 510, color: 'var(--color-accent)' }}>{t}</span> },
    { title: '样本量', dataIndex: 'sampleSize', key: 'sampleSize', render: v => <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>{v}</span> },
    { title: '更新日期', dataIndex: 'updatedAt', key: 'updatedAt', render: t => <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{t}</span> },
  ];

  return (
    <div className="fade-in" data-component="AdminBaseData">
      <div className="content-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div><h2 className="content-header__title">基础数据管理</h2><p className="content-header__subtitle">维护职位标准库、城市数据、薪资基准等平台基础配置</p></div>
          <Space>
            {activeTab === 'salary' && <Button icon={<Activity size={14} />} onClick={handleSyncSalary}>同步市场数据</Button>}
            <Button type="primary" icon={<Plus size={14} />} onClick={() => antMessage.info('新增功能开发中')}>新增条目</Button>
          </Space>
        </div>
      </div>
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        { key: 'jobs', label: `职位库 (${jobTitles.length})` },
        { key: 'cities', label: `城市数据 (${cities.length})` },
        { key: 'salary', label: `薪资基准 (${benchmarks.length})` },
        { key: 'industry', label: '行业分类' },
        { key: 'education', label: '学历配置' },
      ]} />
      <div style={{ marginTop: 8, marginBottom: 12, display: 'flex', gap: 8 }}>
        <Input.Search placeholder="搜索..." style={{ width: 280 }} value={searchText} onChange={e => setSearchText(e.target.value)} allowClear />
      </div>

      {activeTab === 'jobs' && (
        <Card styles={{ body: { padding: 0 } }}>
          <Table columns={jobColumns} dataSource={jobTitles.filter(j => !searchText || j.name.includes(searchText) || j.category.includes(searchText))} pagination={{ pageSize: 10 }} size="middle" rowKey="id" />
        </Card>
      )}
      {activeTab === 'cities' && (
        <Card styles={{ body: { padding: 0 } }}>
          <Table columns={cityColumns} dataSource={cities.filter(c => !searchText || c.name.includes(searchText))} pagination={false} size="middle" rowKey="id" />
        </Card>
      )}
      {activeTab === 'salary' && (
        <>
          <div className="ai-suggestion-bar" style={{ marginBottom: 12 }}>
            <Sparkles size={16} color="var(--color-accent)" />
            <span className="ai-suggestion-bar__text">AI 建议：深圳前端开发 P50 薪资较上月上浮 5.2%，建议更新基准数据</span>
            <button className="ai-suggestion-bar__action" onClick={handleSyncSalary}>立即更新</button>
          </div>
          <Card styles={{ body: { padding: 0 } }}>
            <Table columns={salaryColumns} dataSource={benchmarks.filter(b => !searchText || b.jobCategory.includes(searchText) || b.city.includes(searchText))} pagination={false} size="middle" rowKey="id" />
          </Card>
        </>
      )}
      {activeTab === 'industry' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[
            { name: '互联网/IT', sub: ['软件开发', '电子商务', '游戏', 'SaaS', '人工智能'], count: 456 },
            { name: '金融', sub: ['银行', '证券', '保险', '基金', ' fintech'], count: 189 },
            { name: '制造业', sub: ['电子制造', '汽车', '机械', '化工'], count: 134 },
            { name: '教育培训', sub: ['在线教育', 'K12', '职业培训', '语言培训'], count: 98 },
            { name: '医疗健康', sub: ['医药', '医疗器械', '医疗服务', '生物技术'], count: 76 },
            { name: '房地产/建筑', sub: ['房地产开发', '建筑设计', '物业管理'], count: 65 },
          ].map((ind, i) => (
            <div key={i} style={{ padding: '16px 20px', background: 'var(--bg-base)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontWeight: 590, fontSize: 15 }}>{ind.name}</span>
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{ind.count} 家企业</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {ind.sub.map((s, j) => <Tag key={j}>{s}</Tag>)}
              </div>
              <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                <Button type="link" size="small" style={{ fontSize: 12, padding: 0 }}>编辑</Button>
                <Button type="link" size="small" style={{ fontSize: 12, padding: 0 }}>添加子类</Button>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'education' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 600 }}>
          {[
            { level: '不限', code: 'none', order: 0, jobCount: 120, description: '不限制学历要求' },
            { level: '大专', code: 'college', order: 1, jobCount: 245, description: '大学专科及以上学历' },
            { level: '本科', code: 'bachelor', order: 2, jobCount: 480, description: '大学本科及以上学历' },
            { level: '硕士', code: 'master', order: 3, jobCount: 86, description: '硕士研究生及以上学历' },
            { level: '博士', code: 'phd', order: 4, jobCount: 12, description: '博士研究生学历' },
          ].map((edu, i) => (
            <div key={i} style={{ padding: '14px 20px', background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontWeight: 590, fontSize: 15 }}>{edu.level}</span>
                  <Tag>{edu.code}</Tag>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>排序：{edu.order}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>{edu.description} · 关联 {edu.jobCount} 个岗位</div>
              </div>
              <Button type="link" size="small" onClick={() => antMessage.info('编辑学历要求')}>编辑</Button>
            </div>
          ))}
        </div>
      )}

      <Modal title="编辑职位" open={!!editModal} onCancel={() => setEditModal(null)} footer={null} width={480}>
        {editModal && (
          <div>
            <div className="form-section">
              <div className="form-section__title">标准职位名称</div>
              <Input defaultValue={editModal.name} size="large" />
            </div>
            <div className="form-section">
              <div className="form-section__title">所属分类</div>
              <Select defaultValue={editModal.category} style={{ width: '100%' }} options={['技术研发', '设计', '产品运营', '数据', '市场销售', '人事行政'].map(c => ({ label: c, value: c }))} />
            </div>
            <div className="form-section">
              <div className="form-section__title">AI别名映射 <AIBadge>AI标准化</AIBadge></div>
              <Select mode="tags" defaultValue={editModal.aliases} style={{ width: '100%' }} placeholder="输入别名后回车添加" />
              <p style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>招聘者输入这些别名时，系统将自动标准化为「{editModal.name}」</p>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <Button onClick={() => setEditModal(null)}>取消</Button>
              <Button type="primary" onClick={() => { antMessage.success('职位信息已更新'); setEditModal(null); }}>保存</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

/* --- Admin AI Service Monitor (Interactive) --- */
const aiServiceMetrics = [
  { time: '00:00', llm: 120, ocr: 45, review: 80, recommend: 200 },
  { time: '04:00', llm: 35, ocr: 12, review: 25, recommend: 60 },
  { time: '08:00', llm: 280, ocr: 95, review: 190, recommend: 450 },
  { time: '10:00', llm: 520, ocr: 180, review: 350, recommend: 680 },
  { time: '12:00', llm: 380, ocr: 120, review: 260, recommend: 520 },
  { time: '14:00', llm: 480, ocr: 165, review: 310, recommend: 620 },
  { time: '16:00', llm: 550, ocr: 190, review: 380, recommend: 710 },
  { time: '18:00', llm: 420, ocr: 140, review: 280, recommend: 560 },
  { time: '20:00', llm: 260, ocr: 80, review: 170, recommend: 380 },
  { time: '22:00', llm: 150, ocr: 50, review: 100, recommend: 240 },
];

const aiAlertLogs = [
  { id: 1, level: 'warning', service: 'LLM服务', message: 'GPT-4o 响应延迟升至 3.2s（阈值 2s），已切换备用模型', time: '10:42', status: 'resolved' },
  { id: 2, level: 'error', service: '内容审核', message: '敏感词库版本过旧（v2.3），已自动更新至 v2.5', time: '09:15', status: 'resolved' },
  { id: 3, level: 'info', service: '推荐引擎', message: '模型热更新完成，推荐准确率从 82.1% 提升至 83.6%', time: '08:30', status: 'info' },
  { id: 4, level: 'warning', service: 'OCR服务', message: '图片识别队列积压 45 件，预计 5 分钟内处理完毕', time: '08:12', status: 'resolved' },
  { id: 5, level: 'error', service: 'LLM服务', message: 'Token 用量接近日限额（已用 82%），触发限流预警', time: '昨天 22:30', status: 'warning' },
  { id: 6, level: 'info', service: '数据分析', message: '薪资基准月度更新任务完成，覆盖 12 城市 8 类别', time: '昨天 03:00', status: 'info' },
];

const AdminAIMonitor = () => {
  const [selectedService, setSelectedService] = useState(null);
  const [alertFilter, setAlertFilter] = useState('all');

  const services = [
    { name: 'LLM 大语言服务', status: 'healthy', uptime: '99.92%', latency: '1.8s', calls: '2,340', icon: <Bot size={20} />, color: 'var(--color-accent)',
      details: { model: 'GPT-4o / Claude 3.5', tokenUsage: '82%', dailyLimit: '500K tokens', queueLength: 3, avgLatency: '1.8s', p99Latency: '3.2s' } },
    { name: 'OCR 文字识别', status: 'healthy', uptime: '99.98%', latency: '0.6s', calls: '892', icon: <Eye size={20} />, color: 'var(--color-primary)',
      details: { model: 'PaddleOCR v4', accuracy: '96.8%', queueLength: 0, avgLatency: '0.6s', p99Latency: '1.2s', processed: '1,240张/日' } },
    { name: '内容审核引擎', status: 'healthy', uptime: '99.95%', latency: '0.4s', calls: '1,560', icon: <Shield size={20} />, color: 'var(--color-success)',
      details: { model: '自研 + 敏感词库 v2.5', autoPassRate: '67.3%', blockRate: '8.2%', queueLength: 0, avgLatency: '0.4s', falsePositive: '2.1%' } },
    { name: '推荐引擎', status: 'healthy', uptime: '99.90%', latency: '0.3s', calls: '4,280', icon: <Sparkles size={20} />, color: 'var(--color-warning)',
      details: { model: 'DeepFM + BERT', accuracy: '83.6%', ctrLift: '+12.5%', queueLength: 0, avgLatency: '0.3s', dailyRequests: '4,280' } },
  ];

  const filteredAlerts = alertFilter === 'all' ? aiAlertLogs :
    alertFilter === 'error' ? aiAlertLogs.filter(a => a.level === 'error') :
    alertFilter === 'warning' ? aiAlertLogs.filter(a => a.level === 'warning') :
    aiAlertLogs.filter(a => a.level === 'info');

  return (
    <div className="fade-in" data-component="AdminAIMonitor">
      <div className="content-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div><h2 className="content-header__title">AI 服务监控</h2><p className="content-header__subtitle">实时监控AI服务运行状态、性能指标和异常告警</p></div>
          <Space>
            <Tag color="success" style={{ padding: '4px 12px', fontSize: 12 }}><span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-success)', display: 'inline-block', marginRight: 6 }} />全部服务正常</Tag>
            <Button icon={<Activity size={14} />} onClick={() => antMessage.success('监控数据已刷新')}>刷新</Button>
          </Space>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }} data-component="ServiceStatusCards">
        {services.map((svc, i) => (
          <div key={i} style={{ background: 'var(--bg-base)', borderRadius: 'var(--radius-lg)', padding: '20px', border: '1px solid var(--border-light)', cursor: 'pointer', transition: 'all 0.2s', boxShadow: selectedService === i ? '0 0 0 2px var(--color-primary)' : 'var(--shadow-sm)' }}
            onClick={() => setSelectedService(selectedService === i ? null : i)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 'var(--radius-md)', background: svc.color + '15', color: svc.color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{svc.icon}</div>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: svc.status === 'healthy' ? 'var(--color-success)' : 'var(--color-error)', display: 'inline-block' }} />
            </div>
            <div style={{ fontWeight: 590, fontSize: 14, marginBottom: 4 }}>{svc.name}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-tertiary)' }}>
              <span>可用率 {svc.uptime}</span><span>延迟 {svc.latency}</span>
            </div>
            <div style={{ fontSize: 20, fontWeight: 590, color: svc.color, marginTop: 8 }}>{svc.calls}<span style={{ fontSize: 11, fontWeight: 400, color: 'var(--text-tertiary)', marginLeft: 4 }}>次/日</span></div>
          </div>
        ))}
      </div>

      {selectedService !== null && (
        <div style={{ background: 'var(--bg-base)', borderRadius: 'var(--radius-lg)', padding: '20px 24px', border: '1px solid var(--border-light)', marginBottom: 24, boxShadow: 'var(--shadow-sm)' }} data-component="ServiceDetail">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h4 style={{ margin: 0, fontWeight: 590, display: 'flex', alignItems: 'center', gap: 8 }}>{services[selectedService].name} <Tag color="success">运行正常</Tag></h4>
            <Button size="small" onClick={() => setSelectedService(null)}>收起</Button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
            {Object.entries(services[selectedService].details).map(([key, val]) => {
              const labels = { model: '模型/版本', tokenUsage: 'Token用量', dailyLimit: '日限额', queueLength: '队列积压', avgLatency: '平均延迟', p99Latency: 'P99延迟', accuracy: '准确率', processed: '日处理量', autoPassRate: '自动通过率', blockRate: '拦截率', falsePositive: '误报率', ctrLift: 'CTR提升', dailyRequests: '日请求量' };
              return (
                <div key={key} style={{ padding: '12px 16px', background: 'var(--bg-muted)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>{labels[key] || key}</div>
                  <div style={{ fontSize: 16, fontWeight: 590, color: 'var(--text-primary)' }}>{val}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="chart-card">
          <div className="chart-card__title">今日API调用量趋势</div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={aiServiceMetrics}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="time" tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-tertiary)' }} axisLine={false} tickLine={false} />
              <ReTooltip contentStyle={{ borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 12 }} />
              <Area type="monotone" dataKey="llm" stroke="var(--color-accent)" fill="rgba(124,92,252,0.1)" strokeWidth={2} name="LLM" />
              <Area type="monotone" dataKey="recommend" stroke="var(--color-primary)" fill="rgba(22,119,255,0.08)" strokeWidth={2} name="推荐引擎" />
              <Area type="monotone" dataKey="review" stroke="var(--color-success)" fill="rgba(82,196,26,0.08)" strokeWidth={1.5} name="内容审核" />
              <Area type="monotone" dataKey="ocr" stroke="var(--color-warning)" fill="rgba(250,173,20,0.08)" strokeWidth={1.5} name="OCR" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <div className="chart-card__title">模型性能指标</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
            {[
              { label: 'JD生成质量评分', value: 87, target: '目标≥85', good: true },
              { label: '智能回复采纳率', value: 42, target: '目标≥40%', good: true },
              { label: '内容审核准确率', value: 95, target: '目标≥93%', good: true },
              { label: '简历解析完整度', value: 78, target: '目标≥80%', good: false },
              { label: '岗位推荐点击率', value: 18, target: '目标≥15%', good: true },
              { label: '薪资建议准确度', value: 82, target: '目标≥80%', good: true },
            ].map((m, i) => (
              <div key={i}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 13, fontWeight: 450 }}>{m.label}</span>
                  <span style={{ fontSize: 13, fontWeight: 590, color: m.good ? 'var(--color-success)' : 'var(--color-warning)' }}>{m.value}%</span>
                </div>
                <Progress percent={m.value} showInfo={false} strokeColor={m.good ? 'var(--color-success)' : 'var(--color-warning)'} size="small" />
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{m.target}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div data-component="AlertLogs">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h4 style={{ margin: 0, fontWeight: 590, display: 'flex', alignItems: 'center', gap: 8 }}><AlertTriangle size={16} color="var(--color-warning)" />告警日志</h4>
          <Radio.Group size="small" value={alertFilter} onChange={e => setAlertFilter(e.target.value)}>
            <Radio.Button value="all">全部</Radio.Button>
            <Radio.Button value="error">错误</Radio.Button>
            <Radio.Button value="warning">警告</Radio.Button>
            <Radio.Button value="info">信息</Radio.Button>
          </Radio.Group>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filteredAlerts.map(log => {
            const levelMap = { error: { color: 'var(--color-error)', bg: 'var(--color-error-soft)', icon: <XCircle size={14} />, label: '错误' }, warning: { color: 'var(--color-warning)', bg: 'var(--color-warning-soft)', icon: <AlertTriangle size={14} />, label: '警告' }, info: { color: 'var(--color-primary)', bg: 'var(--color-primary-soft)', icon: <Activity size={14} />, label: '信息' } };
            const lv = levelMap[log.level];
            return (
              <div key={log.id} style={{ background: 'var(--bg-base)', borderRadius: 'var(--radius-md)', padding: '14px 18px', border: `1px solid ${log.level === 'error' ? 'rgba(255,77,79,0.15)' : 'var(--border-light)'}`, display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ width: 28, height: 28, borderRadius: 'var(--radius-sm)', background: lv.bg, color: lv.color, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{lv.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <Tag style={{ fontSize: 10, padding: '0 6px' }}>{log.service}</Tag>
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{log.time}</span>
                    {log.status === 'resolved' && <Tag color="success" style={{ fontSize: 10, padding: '0 6px' }}>已恢复</Tag>}
                    {log.status === 'warning' && <Tag color="warning" style={{ fontSize: 10, padding: '0 6px' }}>持续关注</Tag>}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{log.message}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div style={{ marginTop: 24, padding: '16px 20px', background: 'var(--color-accent-soft)', borderRadius: 'var(--radius-lg)', border: '1px solid rgba(124,92,252,0.12)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}><Sparkles size={16} color="var(--color-accent)" /><span style={{ fontSize: 14, fontWeight: 510, color: 'var(--color-accent)' }}>AI 资源用量概览</span></div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {[
            { label: 'LLM Token 今日用量', value: '410K', sub: '日限额 500K · 82%', pct: 82 },
            { label: 'OCR 今日调用', value: '892', sub: '日限额 5,000 · 18%', pct: 18 },
            { label: '审核队列积压', value: '3', sub: '正常范围 ≤10', pct: 30 },
            { label: '推荐引擎 QPS', value: '48', sub: '峰值承载 200 · 24%', pct: 24 },
          ].map((m, i) => (
            <div key={i}>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 4 }}>{m.label}</div>
              <div style={{ fontSize: 22, fontWeight: 590, color: 'var(--color-accent)', marginBottom: 6 }}>{m.value}</div>
              <Progress percent={m.pct} showInfo={false} strokeColor={m.pct > 70 ? 'var(--color-warning)' : 'var(--color-accent)'} size="small" />
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{m.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

/* ============================================================
   MAIN APP WITH ROUTING
   ============================================================ */
const recruiterNav = [
  { title: '', items: [
    { path: '/recruiter', label: '工作台', icon: <LayoutDashboard size={18} /> },
    { path: '/recruiter/job/create', label: '发布岗位', icon: <Plus size={18} /> },
    { path: '/recruiter/job/upload', label: '批量上传', icon: <Upload size={18} /> },
    { path: '/recruiter/jobs', label: '我的岗位', icon: <Briefcase size={18} /> },
    { path: '/recruiter/messages', label: '消息中心', icon: <MessageSquare size={18} />, badge: 3 },
  ]},
  { title: '更多', items: [
    { path: '/recruiter', label: '数据统计', icon: <BarChart3 size={18} /> },
    { path: '/recruiter', label: '账号设置', icon: <Settings size={18} /> },
  ]}
];

const adminNav = [
  { title: '', items: [
    { path: '/admin', label: '数据看板', icon: <LayoutDashboard size={18} /> },
    { path: '/admin/review', label: '审核管理', icon: <FileCheck size={18} />, badge: 8 },
  ]},
  { title: '系统', items: [
    { path: '/admin/users', label: '用户管理', icon: <Users size={18} /> },
    { path: '/admin/data', label: '基础数据', icon: <Settings size={18} /> },
    { path: '/admin/ai-monitor', label: 'AI服务监控', icon: <Activity size={18} /> },
  ]}
];

const RoleSwitcher = ({ currentRole, onSwitch }) => (
  <div className="role-switcher" data-component="RoleSwitcher">
    <span style={{ color: 'rgba(255,255,255,0.45)', fontSize: 12, marginRight: 8, fontWeight: 510 }}>角色切换</span>
    {[
      { role: 'recruiter', label: '招聘者端', icon: <Building2 size={14} /> },
      { role: 'seeker', label: '应聘者端', icon: <UserCircle size={14} /> },
      { role: 'admin', label: '管理后台', icon: <Shield size={14} /> },
    ].map(r => (
      <button key={r.role} className={`role-switcher__btn ${currentRole === r.role ? 'role-switcher__btn--active' : ''}`} onClick={() => onSwitch(r.role)}>
        {r.icon} {r.label}
      </button>
    ))}
  </div>
);

const SeekerLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  return (
    <div className="dashboard-layout" style={{ flexDirection: 'column' }} data-component="SeekerLayout">
      <div style={{ height: 56, background: 'var(--bg-base)', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="sidebar__brand-icon" style={{ width: 28, height: 28, borderRadius: 6 }}><Briefcase size={14} /></div>
          <span style={{ fontWeight: 590, fontSize: 16 }}>空岗平台</span>
        </div>
        <nav style={{ display: 'flex', gap: 24, fontSize: 13, fontWeight: 450 }}>
          <a onClick={(e) => { e.preventDefault(); navigate('/seeker'); }} style={{ color: location.pathname === '/seeker' ? 'var(--text-primary)' : 'var(--text-secondary)', textDecoration: 'none', cursor: 'pointer' }}>首页</a>
          <a onClick={(e) => { e.preventDefault(); navigate('/seeker/subscriptions'); }} style={{ color: location.pathname.includes('subscriptions') ? 'var(--text-primary)' : 'var(--text-secondary)', textDecoration: 'none', cursor: 'pointer' }}>订阅</a>
          <a onClick={(e) => { e.preventDefault(); navigate('/seeker/messages'); }} style={{ color: location.pathname.includes('messages') ? 'var(--text-primary)' : 'var(--text-secondary)', textDecoration: 'none', cursor: 'pointer' }}>消息</a>
        </nav>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Badge count={5}><Bell size={18} color="var(--text-secondary)" style={{ cursor: 'pointer' }} /></Badge>
          <Avatar size={30} style={{ background: 'var(--color-success)', fontSize: 12 }}>陈</Avatar>
        </div>
      </div>
      <main className="content-area" style={{ flex: 1, overflow: 'auto' }}>{children}</main>
    </div>
  );
};

function AppRoutes() {
  const { currentRole, setCurrentRole } = useContext(AppState);
  const navigate = useNavigate();

  const handleRoleSwitch = (role) => {
    setCurrentRole(role);
    navigate(`/${role}`);
  };

  return (
    <div className="app-root" data-component="AppRoot">
      <RoleSwitcher currentRole={currentRole} onSwitch={handleRoleSwitch} />
      <Routes>
        <Route path="/" element={<Navigate to="/recruiter" replace />} />
        <Route path="/recruiter/*" element={
          <SidebarLayout brand="空岗平台" nav={recruiterNav}>
            <Routes>
              <Route index element={<RecruiterDashboard />} />
              <Route path="job/create" element={<RecruiterJobCreate />} />
              <Route path="job/upload" element={<RecruiterJobUpload />} />
              <Route path="jobs" element={<RecruiterJobs />} />
              <Route path="messages" element={<RecruiterMessages />} />
            </Routes>
          </SidebarLayout>
        } />
        <Route path="/seeker/*" element={
          <SeekerLayout>
            <Routes>
              <Route index element={<SeekerHome />} />
              <Route path="job/:id" element={<SeekerJobDetail />} />
              <Route path="subscriptions" element={<SeekerSubscriptions />} />
              <Route path="messages" element={<SeekerMessages />} />
            </Routes>
          </SeekerLayout>
        } />
        <Route path="/admin/*" element={
          <SidebarLayout brand="管理后台" nav={adminNav}>
            <Routes>
              <Route index element={<AdminDashboard />} />
              <Route path="review" element={<AdminReview />} />
              <Route path="users" element={<AdminUserManagement />} />
              <Route path="data" element={<AdminBaseData />} />
              <Route path="ai-monitor" element={<AdminAIMonitor />} />
            </Routes>
          </SidebarLayout>
        } />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppRoutes />
    </AppProvider>
  );
}
