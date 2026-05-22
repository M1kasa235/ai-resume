import { useEffect, useState } from 'react';

import {
  QuestionCircleOutlined,
  SearchOutlined,
  DeleteOutlined,
  PlusOutlined,
  EditOutlined,
  DatabaseOutlined,
  FileProtectOutlined,
} from '@ant-design/icons';
import {
  Table,
  Card,
  Button,
  Tabs,
  Tag,
  Space,
  Input,
  message,
  Modal,
  Form,
  Select,
  InputNumber,
  Switch,
  Popconfirm,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { adminApi, questionApi, jobApi } from '@services/api';
import type { Question, Job } from '@/types/api';

import styles from './Admin.module.scss';
import KnowledgeTab from './KnowledgeTab';
import ResumeTab from './ResumeTab';

// ==================== 题目管理 Tab ====================
function QuestionsTab() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [form] = Form.useForm();

  const fetchQuestions = async (p: number = 1) => {
    setLoading(true);
    try {
      const res = await questionApi.getQuestions({ page: p, page_size: 20 });
      const d = res as any;
      setQuestions(d.items || []);
      setTotal(d.total || 0);
      setPage(p);
    } catch {
      message.error('获取题目列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, []);

  const handleCreate = () => {
    setEditingQuestion(null);
    form.resetFields();
    form.setFieldsValue({ difficulty: 'medium', type: 'single_choice' });
    setModalOpen(true);
  };

  const handleEdit = (q: Question) => {
    setEditingQuestion(q);
    form.setFieldsValue({
      category_id: q.category_id,
      type: q.type,
      difficulty: q.difficulty,
      title: q.title,
      content: q.content,
      options: q.options ? JSON.stringify(q.options) : undefined,
      correct_answer: q.correct_answer,
      explanation: q.explanation,
      tags: q.tags,
      company_tags: q.company_tags,
      is_hot: q.is_hot,
    });
    setModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await adminApi.deleteQuestion(id);
      message.success('删除成功');
      fetchQuestions(page);
    } catch {
      message.error('删除失败');
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (values.options && typeof values.options === 'string') {
        try {
          values.options = JSON.parse(values.options);
        } catch {
          values.options = values.options.split('\n').filter(Boolean);
        }
      }
      if (editingQuestion) {
        await adminApi.updateQuestion(editingQuestion.id, values);
        message.success('更新成功');
      } else {
        await adminApi.createQuestion(values);
        message.success('创建成功');
      }
      setModalOpen(false);
      fetchQuestions(page);
    } catch {
      message.error('操作失败，请检查表单');
    }
  };

  const typeLabels: Record<string, string> = {
    single_choice: '单选题',
    multiple_choice: '多选题',
    essay: '问答题',
    coding: '编程题',
    open: '开放题',
  };

  const difficultyColors: Record<string, string> = {
    easy: 'green',
    medium: 'orange',
    hard: 'red',
  };

  const columns: ColumnsType<Question> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '题型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (t: string) => typeLabels[t] || t,
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 80,
      render: (d: string) => (
        <Tag color={difficultyColors[d] || 'default'}>{d}</Tag>
      ),
    },
    {
      title: '标签',
      key: 'tags',
      width: 200,
      render: (_: any, record: Question) => (
        <div className={styles.tagList}>
          {(record.tags || []).slice(0, 3).map((t) => (
            <Tag key={t} style={{ margin: 0 }}>
              {t}
            </Tag>
          ))}
          {(record.company_tags || []).slice(0, 2).map((t) => (
            <Tag key={t} color="purple" style={{ margin: 0 }}>
              {t}
            </Tag>
          ))}
        </div>
      ),
    },
    {
      title: '热门',
      dataIndex: 'is_hot',
      key: 'is_hot',
      width: 60,
      render: (v: boolean) => (v ? <Tag color="red">Hot</Tag> : null),
    },
    {
      title: '操作',
      key: 'action',
      width: 140,
      render: (_: any, record: Question) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定删除此题？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className={styles.toolbar}>
        <span style={{ fontWeight: 500 }}>题目管理</span>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增题目
        </Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={questions}
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: fetchQuestions,
          showTotal: (t) => `共 ${t} 条`,
        }}
        size="small"
      />

      <Modal
        title={editingQuestion ? '编辑题目' : '新增题目'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        width={720}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          className={styles.questionForm}
        >
          <Form.Item name="category_id" label="分类ID" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="type" label="题型" rules={[{ required: true }]}>
            <Select
              options={[
                { value: 'single_choice', label: '单选题' },
                { value: 'multiple_choice', label: '多选题' },
                { value: 'essay', label: '问答题' },
                { value: 'coding', label: '编程题' },
                { value: 'open', label: '开放题' },
              ]}
            />
          </Form.Item>
          <Form.Item name="difficulty" label="难度">
            <Select
              options={[
                { value: 'easy', label: '简单' },
                { value: 'medium', label: '中等' },
                { value: 'hard', label: '困难' },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="title"
            label="题目标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="content" label="题目内容">
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="options" label="选项（JSON数组或每行一个）">
            <Input.TextArea rows={4} placeholder='["选项A", "选项B", "选项C", "选项D"]' />
          </Form.Item>
          <Form.Item name="correct_answer" label="正确答案">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="explanation" label="解析">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入标签后回车" />
          </Form.Item>
          <Form.Item name="company_tags" label="公司标签">
            <Select mode="tags" placeholder="输入公司标签后回车" />
          </Form.Item>
          <Form.Item name="is_hot" label="热门题目" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

// ==================== 岗位管理 Tab ====================
const companyStageOptions = [
  { value: '未融资', label: '未融资' },
  { value: '天使轮', label: '天使轮' },
  { value: 'A轮', label: 'A轮' },
  { value: 'B轮', label: 'B轮' },
  { value: 'C轮', label: 'C轮' },
  { value: 'D轮及以上', label: 'D轮及以上' },
  { value: '上市公司', label: '上市公司' },
  { value: '不需要融资', label: '不需要融资' },
];

const companySizeOptions = [
  { value: '少于15人', label: '少于15人' },
  { value: '15-50人', label: '15-50人' },
  { value: '50-150人', label: '50-150人' },
  { value: '150-500人', label: '150-500人' },
  { value: '500-2000人', label: '500-2000人' },
  { value: '2000人以上', label: '2000人以上' },
];

const educationOptions = [
  { value: '不限', label: '不限' },
  { value: '高中', label: '高中' },
  { value: '大专', label: '大专' },
  { value: '本科', label: '本科' },
  { value: '硕士', label: '硕士' },
  { value: '博士', label: '博士' },
];

function JobsTab() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);
  const [keyword, setKeyword] = useState('');
  const [form] = Form.useForm();

  const fetchJobs = async (p: number = 1) => {
    setLoading(true);
    try {
      const res = await jobApi.getJobs({ page: p, page_size: 20, keyword });
      const d = res as any;
      setJobs(d.items || []);
      setTotal(d.total || 0);
      setPage(p);
    } catch {
      message.error('获取岗位列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleSearch = () => {
    fetchJobs(1);
  };

  const handleCreate = () => {
    setEditingJob(null);
    form.resetFields();
    form.setFieldsValue({ salary_months: 12, education_requirement: '不限', is_active: true });
    setModalOpen(true);
  };

  const handleEdit = (job: Job) => {
    setEditingJob(job);
    form.setFieldsValue({
      title: job.title,
      company_name: job.company_name,
      company_logo: job.company_logo,
      company_stage: job.company_stage,
      company_size: job.company_size,
      description: job.description,
      requirements: job.requirements,
      salary_min: job.salary_min,
      salary_max: job.salary_max,
      salary_months: job.salary_months,
      city: job.city,
      district: job.district,
      address: job.address,
      experience_min: job.experience_min,
      experience_max: job.experience_max,
      education_requirement: job.education_requirement,
      skills_required: job.skills_required,
      tags: job.tags,
      is_urgent: job.is_urgent,
      is_active: job.is_active,
    });
    setModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await jobApi.deleteJob(id);
      message.success('删除成功');
      fetchJobs(page);
    } catch {
      message.error('删除失败');
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      if (editingJob) {
        await jobApi.updateJob(editingJob.id, values);
        message.success('更新成功');
      } else {
        await jobApi.createJob(values);
        message.success('创建成功');
      }
      setModalOpen(false);
      fetchJobs(1);
    } catch {
      message.error('操作失败，请检查表单');
    }
  };

  const columns: ColumnsType<Job> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '职位名称',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      width: 180,
    },
    {
      title: '公司',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 140,
      ellipsis: true,
    },
    {
      title: '城市',
      dataIndex: 'city',
      key: 'city',
      width: 90,
    },
    {
      title: '薪资',
      key: 'salary',
      width: 120,
      render: (_: any, record: Job) => record.salary_display || `${record.salary_min || '?'}-${record.salary_max || '?'}K`,
    },
    {
      title: '经验',
      dataIndex: 'experience_display',
      key: 'experience_display',
      width: 100,
    },
    {
      title: '学历',
      dataIndex: 'education_requirement',
      key: 'education_requirement',
      width: 70,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 70,
      render: (v: boolean) => (v ? <Tag color="green">上架</Tag> : <Tag color="default">下架</Tag>),
    },
    {
      title: '操作',
      key: 'action',
      width: 140,
      render: (_: any, record: Job) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确定删除此岗位？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className={styles.toolbar}>
        <Space>
          <span style={{ fontWeight: 500 }}>岗位管理</span>
          <Input.Search
            placeholder="搜索职位/公司"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onSearch={handleSearch}
            style={{ width: 240 }}
            allowClear
          />
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新增岗位
        </Button>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={jobs}
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: fetchJobs,
          showTotal: (t) => `共 ${t} 条`,
        }}
        size="small"
      />

      <Modal
        title={editingJob ? '编辑岗位' : '新增岗位'}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ maxWidth: 760 }}>
          <Form.Item name="title" label="职位名称" rules={[{ required: true, message: '请输入职位名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="company_name" label="公司名称" rules={[{ required: true, message: '请输入公司名称' }]}>
            <Input />
          </Form.Item>
          <Space style={{ width: '100%' }} size={16}>
            <Form.Item name="company_stage" label="融资阶段">
              <Select options={companyStageOptions} style={{ width: 160 }} allowClear />
            </Form.Item>
            <Form.Item name="company_size" label="公司规模">
              <Select options={companySizeOptions} style={{ width: 160 }} allowClear />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size={16}>
            <Form.Item name="city" label="城市">
              <Input style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="district" label="区域">
              <Input style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="address" label="详细地址">
              <Input style={{ width: 240 }} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size={16}>
            <Form.Item name="salary_min" label="最低薪资(K)">
              <InputNumber min={0} style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="salary_max" label="最高薪资(K)">
              <InputNumber min={0} style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="salary_months" label="薪资月数">
              <InputNumber min={1} max={24} style={{ width: 100 }} />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size={16}>
            <Form.Item name="experience_min" label="最低经验(年)">
              <InputNumber min={0} max={15} style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="experience_max" label="最高经验(年)">
              <InputNumber min={0} max={15} style={{ width: 120 }} />
            </Form.Item>
            <Form.Item name="education_requirement" label="学历要求">
              <Select options={educationOptions} style={{ width: 120 }} />
            </Form.Item>
          </Space>
          <Form.Item name="description" label="职位描述">
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="requirements" label="任职要求">
            <Input.TextArea rows={4} />
          </Form.Item>
          <Form.Item name="skills_required" label="技能要求">
            <Select mode="tags" placeholder="输入技能后回车" />
          </Form.Item>
          <Form.Item name="tags" label="标签">
            <Select mode="tags" placeholder="输入标签后回车" />
          </Form.Item>
          <Space size={16}>
            <Form.Item name="is_urgent" label="急聘" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item name="is_active" label="上架" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  );
}

// ==================== Admin Page ====================
export default function AdminPage() {
  return (
    <div className={styles.adminPage}>
      <Card>
        <Tabs
          defaultActiveKey="knowledge"
          items={[
            {
              key: 'knowledge',
              label: (
                <span>
                  <DatabaseOutlined /> 知识库管理
                </span>
              ),
              children: <KnowledgeTab />,
            },
            {
              key: 'resume',
              label: (
                <span>
                  <FileProtectOutlined /> 简历管理
                </span>
              ),
              children: <ResumeTab />,
            },
            {
              key: 'jobs',
              label: (
                <span>
                  <SearchOutlined /> 岗位管理
                </span>
              ),
              children: <JobsTab />,
            },
            {
              key: 'questions',
              label: (
                <span>
                  <QuestionCircleOutlined /> 题目管理
                </span>
              ),
              children: <QuestionsTab />,
            },
          ]}
        />
      </Card>
    </div>
  );
}
