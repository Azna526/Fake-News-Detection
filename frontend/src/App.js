import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Progress } from './components/ui/progress';
import { Separator } from './components/ui/separator';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Globe, 
  FileText, 
  TrendingUp, 
  Shield, 
  Eye,
  Clock,
  Loader2,
  ExternalLink
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState('text');
  const [textContent, setTextContent] = useState('');
  const [urlContent, setUrlContent] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/history`);
      setHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };

  const analyzeContent = async () => {
    if (!textContent.trim() && !urlContent.trim()) {
      setError('Please provide either text content or a URL to analyze');
      return;
    }

    setIsAnalyzing(true);
    setError('');
    setAnalysis(null);

    try {
      const requestData = {
        analysis_type: 'comprehensive'
      };

      if (activeTab === 'text' && textContent.trim()) {
        requestData.content = textContent.trim();
      } else if (activeTab === 'url' && urlContent.trim()) {
        requestData.url = urlContent.trim();
      }

      const response = await axios.post(`${API}/analyze`, requestData);
      setAnalysis(response.data);
      await fetchHistory(); // Refresh history
      
      // Clear inputs after successful analysis
      setTextContent('');
      setUrlContent('');
    } catch (error) {
      setError(error.response?.data?.detail || 'Analysis failed. Please try again.');
      console.error('Analysis error:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getClassificationColor = (classification) => {
    switch (classification) {
      case 'Real News': return 'bg-green-100 text-green-800 border-green-200';
      case 'Fake News': return 'bg-red-100 text-red-800 border-red-200';
      case 'Misleading': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'Satirical': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'Opinion': return 'bg-purple-100 text-purple-800 border-purple-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getBiasColor = (score) => {
    if (score <= 3) return 'text-green-600';
    if (score <= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">HoaxHunter</h1>
                <p className="text-sm text-slate-600">AI-Powered Fake News Detection</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm text-slate-600">
              <Eye className="w-4 h-4" />
              <span>Real-time Analysis</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Analysis Input Section */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center space-x-2 text-slate-800">
                  <FileText className="w-5 h-5 text-blue-600" />
                  <span>Content Analysis</span>
                </CardTitle>
                <CardDescription>
                  Enter text content or provide a URL to analyze for fake news, bias, and credibility
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-2 mb-6">
                    <TabsTrigger value="text" className="flex items-center space-x-2">
                      <FileText className="w-4 h-4" />
                      <span>Text Content</span>
                    </TabsTrigger>
                    <TabsTrigger value="url" className="flex items-center space-x-2">
                      <Globe className="w-4 h-4" />
                      <span>URL Analysis</span>
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="text" className="space-y-4">
                    <Textarea
                      placeholder="Paste the news article or content you want to analyze here..."
                      value={textContent}
                      onChange={(e) => setTextContent(e.target.value)}
                      className="min-h-[200px] resize-none border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </TabsContent>

                  <TabsContent value="url" className="space-y-4">
                    <Input
                      type="url"
                      placeholder="https://example.com/news-article"
                      value={urlContent}
                      onChange={(e) => setUrlContent(e.target.value)}
                      className="border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                    />
                    <p className="text-sm text-slate-600">
                      Enter a URL to automatically extract and analyze the article content
                    </p>
                  </TabsContent>
                </Tabs>

                {error && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800">{error}</AlertDescription>
                  </Alert>
                )}

                <Button 
                  onClick={analyzeContent}
                  disabled={isAnalyzing || (!textContent.trim() && !urlContent.trim())}
                  className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium py-3 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing Content...
                    </>
                  ) : (
                    <>
                      <Shield className="w-4 h-4 mr-2" />
                      Analyze Content
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Analysis Results */}
            {analysis && (
              <div className="space-y-6">
                {/* Main Classification */}
                <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span className="flex items-center space-x-2">
                        {analysis.fake_news_analysis.is_fake ? (
                          <XCircle className="w-5 h-5 text-red-600" />
                        ) : (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        )}
                        <span>Analysis Results</span>
                      </span>
                      <Badge className={getClassificationColor(analysis.fake_news_analysis.classification)}>
                        {analysis.fake_news_analysis.classification}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Confidence Score */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-slate-700">Confidence Score</span>
                        <span className={`text-sm font-bold ${getConfidenceColor(analysis.fake_news_analysis.confidence_score)}`}>
                          {analysis.fake_news_analysis.confidence_score.toFixed(1)}%
                        </span>
                      </div>
                      <Progress 
                        value={analysis.fake_news_analysis.confidence_score} 
                        className="h-2"
                      />
                    </div>

                    {/* Bias Analysis */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-slate-700">Bias Level</span>
                        <span className={`text-sm font-bold ${getBiasColor(analysis.bias_analysis.bias_score)}`}>
                          {analysis.bias_analysis.bias_score.toFixed(1)}/10
                        </span>
                      </div>
                      <Progress 
                        value={analysis.bias_analysis.bias_score * 10} 
                        className="h-2"
                      />
                      <p className="text-xs text-slate-600">{analysis.bias_analysis.bias_type} bias detected</p>
                    </div>

                    {/* Source Credibility */}
                    {analysis.source_credibility && (
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-slate-700">Source Credibility</span>
                          <span className={`text-sm font-bold ${getConfidenceColor(analysis.source_credibility.credibility_score * 10)}`}>
                            {analysis.source_credibility.credibility_score.toFixed(1)}/10
                          </span>
                        </div>
                        <Progress 
                          value={analysis.source_credibility.credibility_score * 10} 
                          className="h-2"
                        />
                      </div>
                    )}

                    <Separator />

                    {/* Overall Assessment */}
                    <div className="bg-slate-50 rounded-lg p-4">
                      <h4 className="font-semibold text-slate-800 mb-2">Overall Assessment</h4>
                      <p className="text-slate-700 text-sm leading-relaxed">{analysis.overall_assessment}</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Detailed Analysis */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Reasoning & Evidence */}
                  <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm">
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center space-x-2">
                        <TrendingUp className="w-5 h-5 text-blue-600" />
                        <span>Analysis Details</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-slate-800 mb-2">Key Reasoning</h4>
                        <ul className="space-y-1">
                          {analysis.fake_news_analysis.reasoning.map((reason, index) => (
                            <li key={index} className="text-sm text-slate-700 flex items-start space-x-2">
                              <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></span>
                              <span>{reason}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {analysis.fake_news_analysis.evidence.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-slate-800 mb-2">Supporting Evidence</h4>
                          <ul className="space-y-1">
                            {analysis.fake_news_analysis.evidence.map((evidence, index) => (
                              <li key={index} className="text-sm text-slate-700 flex items-start space-x-2">
                                <span className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0"></span>
                                <span>{evidence}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {analysis.fake_news_analysis.red_flags.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-slate-800 mb-2">Red Flags</h4>
                          <ul className="space-y-1">
                            {analysis.fake_news_analysis.red_flags.map((flag, index) => (
                              <li key={index} className="text-sm text-red-700 flex items-start space-x-2">
                                <AlertTriangle className="w-3 h-3 text-red-500 mt-1 flex-shrink-0" />
                                <span>{flag}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Bias & Recommendations */}
                  <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm">
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center space-x-2">
                        <Eye className="w-5 h-5 text-purple-600" />
                        <span>Bias & Recommendations</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <h4 className="font-semibold text-slate-800 mb-2">Bias Indicators</h4>
                        <ul className="space-y-1">
                          {analysis.bias_analysis.bias_indicators.map((indicator, index) => (
                            <li key={index} className="text-sm text-slate-700 flex items-start space-x-2">
                              <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></span>
                              <span>{indicator}</span>
                            </li>
                          ))}
                        </ul>
                        <p className="text-xs text-slate-600 mt-2">{analysis.bias_analysis.explanation}</p>
                      </div>

                      <div>
                        <h4 className="font-semibold text-slate-800 mb-2">Recommendations</h4>
                        <ul className="space-y-1">
                          {analysis.recommendations.map((recommendation, index) => (
                            <li key={index} className="text-sm text-slate-700 flex items-start space-x-2">
                              <CheckCircle className="w-3 h-3 text-green-500 mt-1 flex-shrink-0" />
                              <span>{recommendation}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {analysis.source_url && (
                        <div className="pt-2 border-t border-slate-200">
                          <a 
                            href={analysis.source_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center space-x-1 text-blue-600 hover:text-blue-800 text-sm"
                          >
                            <ExternalLink className="w-3 h-3" />
                            <span>View Original Source</span>
                          </a>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </div>

          {/* History Sidebar */}
          <div className="lg:col-span-1">
            <Card className="shadow-lg border-0 bg-white/70 backdrop-blur-sm sticky top-24">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-slate-800">
                  <Clock className="w-5 h-5 text-slate-600" />
                  <span>Recent Analysis</span>
                </CardTitle>
                <CardDescription>Your analysis history</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 max-h-96 overflow-y-auto">
                {history.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-8">No analysis history yet</p>
                ) : (
                  history.map((item, index) => (
                    <div key={index} className="p-3 bg-slate-50 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <Badge className={getClassificationColor(item.analysis.fake_news_analysis.classification)} size="sm">
                          {item.analysis.fake_news_analysis.classification}
                        </Badge>
                        <span className="text-xs text-slate-500">
                          {formatTimestamp(item.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm text-slate-700 line-clamp-2">
                        {item.analysis.content.substring(0, 100)}...
                      </p>
                      <div className="flex justify-between items-center mt-2">
                        <span className={`text-xs font-medium ${getConfidenceColor(item.analysis.fake_news_analysis.confidence_score)}`}>
                          {item.analysis.fake_news_analysis.confidence_score.toFixed(0)}% confidence
                        </span>
                        {item.analysis.source_url && (
                          <ExternalLink className="w-3 h-3 text-slate-400" />
                        )}
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;