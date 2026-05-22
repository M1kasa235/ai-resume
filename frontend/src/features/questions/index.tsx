import { useState, useEffect } from 'react';

import { questionApi } from '@services/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Input,
  Select,
  Button,
  Tag,
  Empty,
  Tabs,
  Modal,
  Radio,
  Space,
  Typography,
  message,
} from 'antd';

import type { Question, PaginatedResponse } from '@/types';
import type { WrongQuestionItem, FavoriteQuestionItem } from '@/types/api';

import styles from './Questions.module.scss';

const { Search } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

export default function Questions() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useState({
    keyword: '',
    difficulty: '' as 'easy' | 'medium' | 'hard' | '',
    question_type: '',
    only_hot: false,
    page: 1,
    page_size: 20,
  });
  const [practiceVisible, setPracticeVisible] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answer, setAnswer] = useState('');
  const [practiceStartAt, setPracticeStartAt] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [submitResult, setSubmitResult] = useState<{
    is_correct: boolean;
    correct_answer?: string;
    explanation?: string;
  } | null>(null);

  // 练习计时器
  useEffect(() => {
    if (!practiceVisible || submitResult) {
      setElapsedSeconds(0);
      return;
    }
    const timer = setInterval(() => {
      if (practiceStartAt) {
        setElapsedSeconds(Math.floor((Date.now() - practiceStartAt) / 1000));
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [practiceVisible, submitResult, practiceStartAt]);

  const { data: questionsData, isLoading } = useQuery({
    queryKey: ['questions', searchParams],
    queryFn: () => {
      const params = {
        ...searchParams,
        difficulty: searchParams.difficulty || undefined,
        question_type: searchParams.question_type || undefined,
        keyword: searchParams.keyword || undefined,
      };
      return questionApi.getQuestions(params);
    },
  });

  // http 拦截器已经提取了 response.data，所以 questionsData 直接是 PaginatedResponse
  const questionsList = questionsData as any as PaginatedResponse<Question> | undefined;

  const { data: wrongQuestionsData } = useQuery({
    queryKey: ['wrong-questions'],
    queryFn: () => questionApi.getWrongQuestions({ page: 1, page_size: 10 }),
  });

  // http 拦截器已经提取了 response.data
  const wrongQuestions = wrongQuestionsData as any as PaginatedResponse<WrongQuestionItem> | undefined;

  const { data: favoriteQuestionsData } = useQuery({
    queryKey: ['favorite-questions'],
    queryFn: () => questionApi.getFavorites({ page: 1, page_size: 10 }),
  });

  // http 拦截器已经提取了 response.data
  const favoriteQuestions = favoriteQuestionsData as any as PaginatedResponse<FavoriteQuestionItem> | undefined;

  const handleSearch = (values: Record<string, string>) => {
    setSearchParams(prev => ({ ...prev, ...values, page: 1 }));
  };

  const submitAnswerMutation = useMutation({
    mutationFn: (payload: { questionId: number; answerText: string; timeSpent?: number }) =>
      questionApi.submitAnswer(payload.questionId, {
        answer: payload.answerText,
        time_spent: payload.timeSpent,
      }),
    onSuccess: (data) => {
      const result = data as unknown as {
        is_correct: boolean;
        correct_answer?: string;
        explanation?: string;
      };
      setSubmitResult(result);
      queryClient.invalidateQueries({ queryKey: ['wrong-questions'] });
      queryClient.invalidateQueries({ queryKey: ['questions'] });
      message.success(result.is_correct ? '回答正确' : '回答已提交');
    },
    onError: () => {
      message.error('提交答案失败，请稍后重试');
    },
  });

  const startPractice = async (questionId: number) => {
    try {
      const detail = await questionApi.getQuestionDetail(questionId);
      setCurrentQuestion(detail as unknown as Question);
      setAnswer('');
      setSubmitResult(null);
      setPracticeStartAt(Date.now());
      setPracticeVisible(true);
    } catch {
      message.error('获取题目详情失败，请稍后重试');
    }
  };

  const closePractice = () => {
    setPracticeVisible(false);
    setCurrentQuestion(null);
    setAnswer('');
    setSubmitResult(null);
    setPracticeStartAt(null);
  };

  const handleSubmitAnswer = () => {
    if (!currentQuestion) return;
    const trimmed = answer.trim();
    if (!trimmed) {
      message.warning('请先输入答案');
      return;
    }

    const elapsedSeconds =
      practiceStartAt && practiceStartAt > 0 ? Math.floor((Date.now() - practiceStartAt) / 1000) : undefined;

    submitAnswerMutation.mutate({
      questionId: currentQuestion.id,
      answerText: trimmed,
      timeSpent: elapsedSeconds,
    });
  };

  const renderDifficulty = (difficulty?: string) => {
    const colors = {
      easy: 'success',
      medium: 'warning',
      hard: 'error',
    };
    const labels = {
      easy: '简单',
      medium: '中等',
      hard: '困难',
    };
    return (
      <Tag color={colors[difficulty as keyof typeof colors] || 'default'}>
        {labels[difficulty as keyof typeof labels] || difficulty}
      </Tag>
    );
  };

  const renderType = (type: string) => {
    const typeLabels = {
      single_choice: '单选题',
      multiple_choice: '多选题',
      true_false: '判断题',
      coding: '编程题',
      essay: '简答题',
    };
    return typeLabels[type as keyof typeof typeLabels] || type;
  };

  const renderQuestionCard = (question: Question) => (
    <Card
      key={question.id}
      className={styles.questionCard}
      title={
        <div className={styles.questionHeader}>
          <span className={styles.questionTitle}>{question.title}</span>
          <div className={styles.questionMeta}>
            {renderDifficulty(question.difficulty)}
            <Tag>{renderType(question.type)}</Tag>
            {question.is_hot && <Tag color="red">热门</Tag>}
          </div>
        </div>
      }
      extra={
        <Button type="primary" onClick={() => startPractice(question.id)}>
          开始练习
        </Button>
      }
    >
      {question.content && (
        <div className={styles.questionContent}>
          <p>{question.content}</p>
        </div>
      )}
      
      {question.tags && question.tags.length > 0 && (
        <div className={styles.questionTags}>
          {question.tags.map((tag, index) => (
            <Tag key={index}>
              {tag}
            </Tag>
          ))}
        </div>
      )}
      
      <div className={styles.questionStats}>
        <span>练习次数: {question.frequency}</span>
        <span>正确率: 85%</span>
      </div>
    </Card>
  );

  return (
    <div className={styles.questions}>
      <h1>题库练习</h1>

      <Card className={styles.searchCard}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索题目"
              allowClear
              onSearch={(value) => handleSearch({ keyword: value })}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="难度"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleSearch({ difficulty: value || '' })}
            >
              <Option value="easy">简单</Option>
              <Option value="medium">中等</Option>
              <Option value="hard">困难</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="题型"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleSearch({ question_type: value || '' })}
            >
              <Option value="single_choice">单选题</Option>
              <Option value="multiple_choice">多选题</Option>
              <Option value="true_false">判断题</Option>
              <Option value="coding">编程题</Option>
              <Option value="essay">简答题</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      <Tabs defaultActiveKey="all" className={styles.tabs}>
        <TabPane tab="全部题目" key="all">
          {isLoading ? (
            <div className={styles.loading}>
              <Empty description="加载中..." />
            </div>
          ) : questionsList?.items?.length ? (
            <Row gutter={[16, 16]}>
              {questionsList.items.map(renderQuestionCard)}
            </Row>
          ) : (
            <Empty description="暂无题目" />
          )}
        </TabPane>

        <TabPane tab="错题本" key="wrong">
          {wrongQuestions?.items?.length ? (
            <Row gutter={[16, 16]}>
              {wrongQuestions.items.map((item: WrongQuestionItem) => (
                <Col xs={24} sm={12} lg={8} key={item.id}>
                  <Card className={styles.wrongQuestionCard}>
                    <div className={styles.wrongQuestionHeader}>
                      <h4>{item.question_title}</h4>
                      <Tag color="error">错题</Tag>
                    </div>
                    <div className={styles.wrongQuestionStats}>
                      <span>错误次数: {item.wrong_count}</span>
                      <span>最后错误: {new Date(item.last_wrong_at).toLocaleDateString()}</span>
                    </div>
                    <Button type="primary" block onClick={() => startPractice(item.question_id)}>
                      重新练习
                    </Button>
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <Empty description="暂无错题" />
          )}
        </TabPane>

        <TabPane tab="收藏题目" key="favorite">
          {favoriteQuestions?.items?.length ? (
            <Row gutter={[16, 16]}>
              {favoriteQuestions.items.map((item: FavoriteQuestionItem) => (
                <Col xs={24} sm={12} lg={8} key={item.id}>
                  <Card className={styles.favoriteQuestionCard}>
                    <div className={styles.favoriteQuestionHeader}>
                      <h4>{item.question_title}</h4>
                      <Tag color="success">已收藏</Tag>
                    </div>
                    <div className={styles.favoriteQuestionMeta}>
                      <span>{item.difficulty}</span>
                      <span>{item.type}</span>
                    </div>
                    <Button type="primary" block onClick={() => startPractice(item.question_id)}>
                      开始练习
                    </Button>
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <Empty description="暂无收藏题目" />
          )}
        </TabPane>
      </Tabs>

      <Modal
        title={currentQuestion ? `题目练习` : '题目练习'}
        open={practiceVisible}
        onCancel={closePractice}
        width={760}
        footer={
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <div>
              {currentQuestion && (
                <span style={{ color: '#999', fontSize: 13 }}>
                  耗时：{Math.floor(elapsedSeconds / 60)}分{elapsedSeconds % 60}秒
                </span>
              )}
            </div>
            <Space>
              <Button onClick={closePractice}>关闭</Button>
              <Button
                type="primary"
                onClick={handleSubmitAnswer}
                loading={submitAnswerMutation.isPending}
                disabled={!currentQuestion || !!submitResult}
              >
                提交答案
              </Button>
            </Space>
          </Space>
        }
      >
        {currentQuestion ? (
          <div className={styles.practicePanel}>
            <div className={styles.practiceMeta}>
              {renderDifficulty(currentQuestion.difficulty)}
              <Tag>{renderType(currentQuestion.type)}</Tag>
            </div>
            <h3 style={{ marginBottom: 16 }}>{currentQuestion.title}</h3>
            {currentQuestion.content && (
              <Typography.Paragraph style={{ background: '#fafafa', padding: 12, borderRadius: 8, lineHeight: 1.8 }}>
                {currentQuestion.content}
              </Typography.Paragraph>
            )}

            {currentQuestion.options?.length ? (
              <Radio.Group
                className={styles.optionGroup}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  {currentQuestion.options.map((option, index) => (
                    <div
                      key={index}
                      className={`${styles.optionItem} ${answer === String(option) ? styles.optionItemActive : ''}`}
                    >
                      <Radio value={String(option)}>
                        {option}
                      </Radio>
                    </div>
                  ))}
                </Space>
              </Radio.Group>
            ) : (
              <Input.TextArea
                rows={6}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="请输入你的答案..."
              />
            )}

            {submitResult && (
              <div className={styles.resultPanel}>
                <Tag color={submitResult.is_correct ? 'success' : 'error'} style={{ marginBottom: 8, fontSize: 13, padding: '2px 12px' }}>
                  {submitResult.is_correct ? '✓ 回答正确' : '✗ 回答错误'}
                </Tag>
                {submitResult.correct_answer && (
                  <Typography.Paragraph>
                    <strong>正确答案：</strong>
                    {submitResult.correct_answer}
                  </Typography.Paragraph>
                )}
                {submitResult.explanation && (
                  <Typography.Paragraph>
                    <strong>解析：</strong>
                    {submitResult.explanation}
                  </Typography.Paragraph>
                )}
              </div>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
