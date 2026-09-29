import { useCallback } from 'react';
import { api } from '@/services/api';
import type { AskAIRequest, AskAIResponse, AnalyzeEmailResponse } from '@/types/ai';

export function useAI() {
  const askAI = useCallback(async (request: AskAIRequest): Promise<AskAIResponse> => {
    return api.askAI(request.question, request.context);
  }, []);

  const analyzeEmail = useCallback(async (emailId: string): Promise<AnalyzeEmailResponse> => {
    return api.analyzeEmail(emailId);
  }, []);

  const getDailyBriefing = useCallback(async () => {
    return api.getDailyBriefing();
  }, []);

  const getEndOfDay = useCallback(async () => {
    return api.getEndOfDay();
  }, []);

  const whatAmIForgetting = useCallback(async () => {
    return api.whatAmIForgetting();
  }, []);

  return {
    askAI,
    analyzeEmail,
    getDailyBriefing,
    getEndOfDay,
    whatAmIForgetting,
  };
}