import createClient from 'openapi-fetch';

import type { components, paths } from '../generated/openapi';
import config from './config';

const api = createClient<paths>({ baseUrl: `${config.api.url}` });

export type LoginParams = components['schemas']['Body_login_for_access_token_token_post'];

export async function login(params: LoginParams) {
  const res = await api.POST('/token', {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params,
    bodySerializer: (body) => new URLSearchParams(body as Record<string, string>),
  });

  if (res.data && !res.error) return res.data;
  else throw new Error(res.error.detail?.map((d) => d.msg).join('; '));
}

export async function me(token: string) {
  const res = await api.GET('/users/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (res.data) return res.data;
  //else throw new Error(res.error.detail?.map((d) => d.msg).join('; '));
}

export async function userProjects(username: string) {
  // API /session should be rewritten at some point
  const res = await api.GET('/session', {
    params: {
      header: { username },
    },
  });

  if (res.data && !res.error) return res.data.projects as string[];
  else throw new Error(res.error.detail?.map((d) => d.msg).join('; '));
}

// export const function createProject(project: ProjectModel,csvContent:string){

//   const rest = await api.POST('/projects/new', {body: {file: csvContent, ...project}} )
// }
