import { Hono } from 'hono'
import { readdir, readFile } from 'node:fs/promises'
import { join } from 'node:path'
import { completion } from '../services/common/llm.service'
import { observer } from '../services/agent/observer.service'
import { setInteractionState } from '../services/agent/agi.service'
import { stateManager } from '../services/agent/state.service'
import { aiService } from '../services/agent/ai.service'
import { taskService } from '../services/agent/task.service'
import { actionService } from '../services/agent/action.service'
import { prompt as answerPrompt } from '../prompts/agent/answer'
import { CoreMessage } from 'ai'
import { v4 as uuidv4 } from 'uuid'
import type { ChatCompletion } from 'openai/resources/chat/completions'

interface TaskOption {
    name: string
    description: string
}

const tasks = new Hono()

// GET /api/tasks - List available special tasks
tasks.get('/', async (c) => {
    const special_tasks_dir = join(process.cwd(), 'specialTasks')
    const entries = await readdir(special_tasks_dir, { withFileTypes: true })
    
    const tasks = await Promise.all(
        entries
            .filter(entry => entry.isDirectory())
            .map(async dir => {
                try {
                    const description_path = join(special_tasks_dir, dir.name, 'taskDescription.md')
                    const content = await readFile(description_path, 'utf-8')
                    return {
                        name: dir.name,
                        description: content.slice(0, 150) + (content.length > 150 ? '...' : '')
                    }
                } catch {
                    return {
                        name: dir.name,
                        description: 'No description available'
                    }
                }
            })
    )
    
    return c.json({ tasks })
})

// POST /api/tasks/:taskName - Run a specific task
tasks.post('/:taskName', async (c) => {
    const task_name = c.req.param('taskName')
    const task_path = join(process.cwd(), 'specialTasks', task_name)
    
    try {
        const description_path = join(task_path, 'taskDescription.md')
        const task_description = await readFile(description_path, 'utf-8')
        
        const request = {
            messages: [{
                role: 'user' as const,
                content: task_description
            }],
            conversation_id: uuidv4(),
            stream: false,
            user: {
                uuid: 'system',
                name: 'system',
                context: 'system',
                environment: '{}'
            },
            model: 'gpt-4o-mini',
            temperature: 0.7,
            max_tokens: 2000
        }

        const conversation_id = await setInteractionState(request)
        const trace = observer.initializeTrace(request.conversation_id || 'general')

        await aiService.think()
        const state = stateManager.getState()

        const messages: CoreMessage[] = [
            { role: 'system' as const, content: answerPrompt(state) },
            ...request.messages as CoreMessage[]
        ]

        const final_generation = observer.startGeneration({ name: 'final_answer', input: messages })
        console.log(final_generation)
        const result = await completion.text({ ...request, messages }, true) as ChatCompletion
        const response = result.choices[0]?.message?.content || 'No response received'

        const final_task = state.interaction.tasks.find(task => task.type === 'final')
        if (final_task) {
            await Promise.all([
                taskService.updateTaskStatus(final_task.uuid, 'completed'),
                state.config.current_action?.uuid && 
                    actionService.updateActionWithResult(
                        state.config.current_action.uuid, 
                        'This turn was completed. '
                    )
            ])
        }

        console.log(response)

        return c.json({ 
            task: task_name,
            response,
            conversation_id
        })
        
    } catch (error: unknown) {
        if ((error as { code: string }).code === 'ENOENT') {
            return c.json({ error: `Task ${task_name} not found` }, 404)
        }
        console.error('Error processing task:', error)
        return c.json({ error: 'Internal server error' }, 500)
    }
})

export default tasks 