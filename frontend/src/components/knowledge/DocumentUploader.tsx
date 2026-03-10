import { useState, useRef, ChangeEvent } from 'react';
import { useKnowledgeStore } from '../../stores/knowledgeStore';
import { Button, Modal, Form, Input, Select, Upload, message } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';

const { Option } = Select;
const { Dragger } = Upload;

export function DocumentUploader() {
  const { uploadDocument } = useKnowledgeStore();
  const [isOpen, setIsOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [form] = Form.useForm();
  const [uploading, setUploading] = useState(false);

  const allowedTypes = ['.pdf', '.docx', '.txt'];
  const maxSize = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(ext)) {
      return `仅支持 ${allowedTypes.join(', ')} 格式的文件`;
    }
    if (file.size > maxSize) {
      return '文件大小不能超过 10MB';
    }
    return null;
  };

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    maxCount: 1,
    accept: '.pdf,.docx,.txt',
    beforeUpload: (file) => {
      const error = validateFile(file);
      if (error) {
        message.error(error);
        return Upload.LIST_IGNORE;
      }
      setFile(file);
      form.setFieldValue('title', file.name.replace(/\.[^/.]+$/, ''));
      return false;
    },
    onRemove: () => {
      setFile(null);
    },
  };

  const handleSubmit = async (values: { title: string; category: string; source: string }) => {
    if (!file) {
      message.warning('请选择文件');
      return;
    }

    setUploading(true);
    try {
      await uploadDocument(file, values.title, values.category || undefined, values.source || undefined);
      message.success('上传成功');
      handleClose();
    } catch (error) {
      // Error is handled in store
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setFile(null);
    form.resetFields();
  };

  return (
    <>
      <Button
        type="primary"
        icon={<UploadOutlined />}
        onClick={() => setIsOpen(true)}
      >
        上传文档
      </Button>

      <Modal
        title="上传文档"
        open={isOpen}
        onCancel={handleClose}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          className="mt-4"
        >
          {/* File Upload */}
          <Form.Item label="选择文件" required>
            <Dragger {...uploadProps}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持 PDF, DOCX, TXT 格式，最大 10MB
              </p>
            </Dragger>
          </Form.Item>

          {/* Title */}
          <Form.Item
            label="标题"
            name="title"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="文档标题" />
          </Form.Item>

          {/* Category */}
          <Form.Item label="分类" name="category">
            <Select placeholder="未分类" allowClear>
              <Option value="law">法律法规</Option>
              <Option value="case">案例分析</Option>
              <Option value="contract">合同范本</Option>
              <Option value="interpretation">司法解释</Option>
            </Select>
          </Form.Item>

          {/* Source */}
          <Form.Item label="来源" name="source">
            <Input placeholder="文档来源（可选）" />
          </Form.Item>

          {/* Actions */}
          <Form.Item className="!mb-0">
            <div className="flex justify-end gap-3">
              <Button onClick={handleClose} disabled={uploading}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={uploading}
                disabled={!file}
              >
                上传
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
