import {z} from 'zod';
import {LangfuseSpanClient} from 'langfuse';
import {stateManager} from '../agent/state.service';
import {documentService} from '../agent/document.service';
import type {DocumentType} from '../agent/document.service';

const envSchema = z.object({
  CENTRAL_API_KEY: z.string(),
});

const API_URL = 'https://centrala.ag3nts.org/report';

interface ReportPayload {
  task: string;
  apikey: string;
  answer: unknown;
}

const centralService = {
  sendReport: async (json_data: unknown, span?: LangfuseSpanClient): Promise<Response> => {
    const env = envSchema.parse(process.env);
    
    const payload: ReportPayload = {
      task: 'JSON',
      apikey: env.CENTRAL_API_KEY,
      answer: json_data
    };

    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Failed to send report: ${response.statusText}`);
    }

    return response;
  },

  execute: async (action: string, payload: Record<string, any>, span?: LangfuseSpanClient): Promise<DocumentType> => {
    const state = stateManager.getState();

    try {
      span?.event({
        name: 'central_report',
        input: { action, payload },
        output: { success: true, action_executed: action }
      });

      if (action !== 'send_report') {
        throw new Error(`Unknown action: ${action}`);
      }

      const response = await centralService.sendReport(payload.data, span);
      const response_data = await response.json();

      return documentService.createDocument({
        conversation_uuid: state.config.conversation_uuid ?? 'unknown',
        source_uuid: state.config.conversation_uuid ?? 'unknown',
        text: `Successfully sent report to central API. Response: ${JSON.stringify(response_data)}`,
        metadata_override: {
          type: 'text',
          source: 'central', 
          description: 'Central API report submission'
        }
      });

    } catch (error) {
      span?.event({
        name: 'central_report_error',
        input: { action, payload },
        output: { error: error instanceof Error ? error.message : 'Unknown error' },
        level: 'ERROR'
      });

      return documentService.createDocument({
        conversation_uuid: state.config.conversation_uuid ?? 'unknown',
        source_uuid: state.config.conversation_uuid ?? 'unknown',
        text: `Failed to send report: ${error instanceof Error ? error.message : 'Unknown error'}`,
        metadata_override: {
          type: 'text',
          source: 'central'
        }
      });
    }
  }
};

export {centralService}; 