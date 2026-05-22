import { useEffect } from 'react';
import { Modal, Form, Input, Select } from 'antd';
import type { KnowledgeDocument } from '@/types/api';

const { TextArea } = Input;

const DOC_TYPE_OPTIONS = [
  { value: 'job', label: '岗位知识 (job)' },
  { value: 'resume_guide', label: '简历指导 (resume_guide)' },
  { value: 'interview', label: '面试知识 (interview)' },
];

interface Props {
  open: boolean;
  editing: KnowledgeDocument | null;
  defaultDocType: string;
  onCancel: () => void;
  onSave: (values: {
    title: string;
    category: string;
    content: string;
    doc_type: string;
  }) => void;
}

export default function DocumentFormModal({
  open,
  editing,
  defaultDocType,
  onCancel,
  onSave,
}: Props) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open) {
      if (editing) {
        form.setFieldsValue({
          title: editing.title,
          category: editing.category || '',
          content: editing.content_full || editing.content || '',
          doc_type: editing.doc_type || defaultDocType,
        });
      } else {
        form.resetFields();
        form.setFieldsValue({ doc_type: defaultDocType, category: '' });
      }
    }
  }, [open, editing, defaultDocType, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      onSave(values);
    } catch {
      // form validation failed
    }
  };

  return (
    <Modal
      title={editing ? '编辑文档' : '新建文档'}
      open={open}
      onOk={handleOk}
      onCancel={onCancel}
      width={720}
      okText="保存"
      cancelText="取消"
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="title"
          label="标题"
          rules={[{ required: true, message: '请输入标题' }]}
        >
          <Input placeholder="文档标题，如：STAR法则详解" />
        </Form.Item>
        <Form.Item name="category" label="分类/标签">
          <Input placeholder="如：简历写作、面试技巧" />
        </Form.Item>
        <Form.Item
          name="doc_type"
          label="所属分区"
          rules={[{ required: true }]}
        >
          <Select options={DOC_TYPE_OPTIONS} />
        </Form.Item>
        <Form.Item
          name="content"
          label="内容"
          rules={[{ required: true, message: '请输入内容' }]}
        >
          <TextArea rows={12} placeholder="文档正文内容（支持 Markdown）" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
