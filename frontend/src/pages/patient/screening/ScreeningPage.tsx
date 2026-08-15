import { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';

interface QuestionItem {
  id: number;
  text: string;
}

interface QuestionnaireDefinition {
  screening_type: 'PHQ-9' | 'GAD-7';
  title: string;
  instructions: string;
  options: string[];
  questions: QuestionItem[];
}

interface ScreeningResult {
  id: string;
  screening_type: string;
  total_score: number;
  severity_band: string;
  created_at: string;
  answers: number[];
}

export default function ScreeningPage() {
  const [activeTab, setActiveTab] = useState<'assess' | 'history'>('assess');
  const [selectedType, setSelectedType] = useState<'PHQ-9' | 'GAD-7'>('PHQ-9');
  const [questionnaire, setQuestionnaire] = useState<QuestionnaireDefinition | null>(null);
  const [answers, setAnswers] = useState<number[]>([]);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [history, setHistory] = useState<ScreeningResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (activeTab === 'assess') {
      fetchQuestions(selectedType);
    } else {
      fetchHistory();
    }
  }, [selectedType, activeTab]);

  const fetchQuestions = async (type: 'PHQ-9' | 'GAD-7') => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await apiClient.get(`/patient/screening/questions/${type}`);
      setQuestionnaire(res.data);
      setAnswers(new Array(res.data.questions.length).fill(-1));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load questionnaire');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.get('/patient/screening/history');
      setHistory(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleOptionSelect = (qIdx: number, value: number) => {
    const updated = [...answers];
    updated[qIdx] = value;
    setAnswers(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (answers.some((a) => a === -1)) {
      setError('Please answer all questions before submitting.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await apiClient.post('/patient/screening/submit', {
        screening_type: selectedType,
        answers: answers
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Submission failed');
    } finally {
      setLoading(false);
    }
  };

  const getBandColor = (band: string) => {
    switch (band) {
      case 'Minimal': return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'Mild': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Moderate': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'Moderately Severe': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'Severe': return 'bg-red-100 text-red-800 border-red-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header & Tabs */}
      <div className="flex justify-between items-center bg-white p-6 rounded-lg shadow-sm">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Self-Screening Assessment</h2>
          <p className="text-sm text-gray-600 mt-1">Standardized questionnaires (PHQ-9 & GAD-7) to monitor mood and anxiety patterns.</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('assess')}
            className={`px-4 py-2 text-sm rounded-md font-medium transition ${
              activeTab === 'assess' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Take Assessment
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 text-sm rounded-md font-medium transition ${
              activeTab === 'history' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            History & Trends
          </button>
        </div>
      </div>

      {error && <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}

      {/* Tab: Take Assessment */}
      {activeTab === 'assess' && (
        <>
          {!result ? (
            <div className="bg-white p-6 rounded-lg shadow-sm space-y-6">
              {/* Questionnaire Selector */}
              <div className="flex space-x-4 border-b border-gray-200 pb-4">
                <button
                  type="button"
                  onClick={() => setSelectedType('PHQ-9')}
                  className={`py-2 px-4 rounded-md font-semibold text-sm transition ${
                    selectedType === 'PHQ-9'
                      ? 'bg-teal-50 text-teal-700 border border-teal-300'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  PHQ-9 (Depression Screening)
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedType('GAD-7')}
                  className={`py-2 px-4 rounded-md font-semibold text-sm transition ${
                    selectedType === 'GAD-7'
                      ? 'bg-teal-50 text-teal-700 border border-teal-300'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  GAD-7 (Anxiety Screening)
                </button>
              </div>

              {loading && <div className="py-8 text-center text-gray-500">Loading questionnaire...</div>}

              {questionnaire && !loading && (
                <form onSubmit={handleSubmit} className="space-y-8">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-800">{questionnaire.title}</h3>
                    <p className="text-sm text-gray-600 mt-1 italic">{questionnaire.instructions}</p>
                  </div>

                  <div className="space-y-6">
                    {questionnaire.questions.map((q, qIdx) => (
                      <div key={q.id} className="p-4 bg-gray-50 rounded-lg border border-gray-100 space-y-3">
                        <p className="font-medium text-gray-800">
                          {qIdx + 1}. {q.text}
                        </p>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" role="group" aria-label={`Question ${qIdx + 1}`}>
                          {questionnaire.options.map((opt, optIdx) => (
                            <button
                              key={optIdx}
                              type="button"
                              onClick={() => handleOptionSelect(qIdx, optIdx)}
                              aria-pressed={answers[qIdx] === optIdx}
                              className={`py-2 px-3 text-xs sm:text-sm rounded border text-center font-medium transition ${
                                answers[qIdx] === optIdx
                                  ? 'bg-teal-700 text-white border-teal-700'
                                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'
                              }`}
                            >
                              {opt}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-end space-x-4 pt-4 border-t border-gray-200">
                    <button
                      type="submit"
                      disabled={loading}
                      className="py-3 px-6 bg-teal-700 text-white font-medium rounded-lg shadow hover:bg-teal-800 disabled:opacity-50 transition"
                    >
                      Submit Assessment
                    </button>
                  </div>
                </form>
              )}
            </div>
          ) : (
            /* Results Screen */
            <div className="bg-white p-8 rounded-lg shadow-sm text-center space-y-6" role="status" aria-live="polite">
              <div className="inline-block p-4 bg-teal-50 rounded-full">
                <span aria-hidden="true" className="text-3xl">📊</span>
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800">Assessment Complete</h3>
                <p className="text-gray-600 mt-1">{result.screening_type} Assessment Result</p>
              </div>

              <div className="max-w-md mx-auto p-6 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
                <p className="text-sm text-gray-500 uppercase tracking-wide font-semibold">Total Score</p>
                <div className="text-4xl font-extrabold text-teal-700">{result.total_score}</div>
                <div className={`inline-block px-4 py-1 text-sm font-semibold rounded-full border ${getBandColor(result.severity_band)}`}>
                  {result.severity_band} Symptom Band
                </div>
              </div>

              <div className="max-w-md mx-auto text-left text-xs text-gray-500 bg-amber-50 p-4 rounded border border-amber-200 space-y-1">
                <p className="font-semibold text-amber-900">Important Clinical Note:</p>
                <p>This result provides a standardized score band for monitoring purposes only. It is not a formal medical diagnosis. If you are feeling distressed or in need of support, please connect with a verified campus counselor or use our panic SOS feature.</p>
              </div>

              <div className="flex justify-center space-x-4 pt-4">
                <button
                  onClick={() => setResult(null)}
                  className="px-5 py-2 bg-teal-600 text-white font-medium rounded-md hover:bg-teal-700 transition"
                >
                  Take Another Assessment
                </button>
                <button
                  onClick={() => setActiveTab('history')}
                  className="px-5 py-2 bg-gray-100 text-gray-700 font-medium rounded-md hover:bg-gray-200 transition"
                >
                  View Score History
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Tab: History */}
      {activeTab === 'history' && (
        <div className="bg-white p-6 rounded-lg shadow-sm space-y-6">
          <h3 className="text-xl font-semibold text-gray-800">Past Screening Submissions</h3>
          {loading && <p className="text-gray-500">Loading history...</p>}

          {!loading && history.length === 0 && (
            <div className="text-center py-8 text-gray-500">No past assessments found. Take your first self-screening!</div>
          )}

          {!loading && history.length > 0 && (
            <div className="divide-y divide-gray-200">
              {history.map((item) => (
                <div key={item.id} className="py-4 flex justify-between items-center">
                  <div>
                    <span className="font-semibold text-gray-800">{item.screening_type}</span>
                    <span className="ml-3 text-xs text-gray-500">{new Date(item.created_at).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-700 text-sm">Score: <strong className="text-teal-700">{item.total_score}</strong></span>
                    <span className={`px-3 py-1 text-xs font-semibold rounded-full border ${getBandColor(item.severity_band)}`}>
                      {item.severity_band}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
