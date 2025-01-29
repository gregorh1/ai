import {z} from 'zod';
import {LangfuseSpanClient} from 'langfuse';
import {stateManager} from '../agent/state.service';
import {documentService} from '../agent/document.service';
import type {DocumentType} from '../agent/document.service';

const apiRequestSchema = z.object({
  endpoint: z.string().url(),
  method: z.enum(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
  body: z.unknown().optional(),
  headers: z.record(z.string()).optional()
});

const apiService = {
  makeRequest: async (request_data: z.infer<typeof apiRequestSchema>, span?: LangfuseSpanClient): Promise<Response> => {
    const validated = apiRequestSchema.parse(request_data);
    
    const response = await fetch(validated.endpoint, {
      method: validated.method,
      headers: {
        'Content-Type': 'application/json',
        ...validated.headers
      },
      body: validated.body ? JSON.stringify(validated.body) : undefined
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response;
  },

  execute: async (action: string, payload: Record<string, any>, span?: LangfuseSpanClient): Promise<DocumentType> => {
    const state = stateManager.getState();

    try {
      span?.event({
        name: 'api_request',
        input: { action, payload },
        output: { success: true, action_executed: action }
      });

      if (action !== 'request') {
        throw new Error(`Unknown action: ${action}`);
      }

      const validated_payload = apiRequestSchema.parse(payload);
      const response = await apiService.makeRequest(validated_payload, span);
      const response_data = await response.json();

      return documentService.createDocument({
        conversation_uuid: state.config.conversation_uuid ?? 'unknown',
        source_uuid: state.config.conversation_uuid ?? 'unknown',
        text: `API Response: ${JSON.stringify(response_data)}`,
        metadata_override: {
          type: 'text',
          source: 'api',
          description: `API request to ${payload.endpoint}`
        }
      });

    } catch (error) {
      span?.event({
        name: 'api_request_error',
        input: { action, payload },
        output: { error: error instanceof Error ? error.message : 'Unknown error' },
        level: 'ERROR'
      });

      return documentService.createDocument({
        conversation_uuid: state.config.conversation_uuid ?? 'unknown',
        source_uuid: state.config.conversation_uuid ?? 'unknown',
        text: `API request failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        metadata_override: {
          type: 'text',
          source: 'api'
        }
      });
    }
  }
};

export {apiService}; 