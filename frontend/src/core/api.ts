import { values } from 'lodash';
import createClient from 'openapi-fetch';
import { useCallback } from 'react';

import type { paths } from '../generated/openapi';
import { AvailableProjectsModel, LoginParams, ProjectDataModel } from '../types';
import { HttpError } from './HTTPError';
import { getAuthHeaders, useAuth } from './auth';
import config from './config';
import { getAsyncMemoData, useAsyncMemo } from './useAsyncMemo';

/**
 * API methods
 */

// all API calls are handled by a client generated by the openapi-fetch library
// It uses the `paths` types generated from the API openApi specifications by running `npm run generate`
const api = createClient<paths>({ baseUrl: `${config.api.url}` });

/**
 * Authentication methods
 * login and me are standard async functions and not hooks.
 * Because they are used directly by the auth centralized mechanism which is itself a hook/context.
 */

/**
 * login : POST a login form data to get an auth token
 * @param params LoginParams
 * @returns an access_token
 */
export async function login(params: LoginParams) {
  const res = await api.POST('/token', {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params,
    bodySerializer: (body) => new URLSearchParams(body as Record<string, string>),
  });

  if (res.data && !res.error) return res.data;
  else {
    console.log(res.error);
    throw new HttpError(
      res.response.status,
      // TODO: debug API type for error, data received are not coherent with types
      res.error.detail + '',
    );
  }
}
/**
 * logout : POST a login form data to get an auth token
 * @param params LoginParams
 * @returns an access_token
 */
export async function logout(token: string) {
  const res = await api.POST('/users/disconnect', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (res.response.status === 200) return true;
  else {
    console.log(res.error);
    throw new HttpError(
      res.response.status,
      // TODO: debug API type for error, data received are not coherent with types
      'could not logout',
    );
  }
}
/**
 * me : GET an authenticated user info
 * @param token
 * @returns user
 */
export async function me(token: string) {
  const res = await api.GET('/users/me', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (res.data) return res.data;
  else throw new HttpError(res.response.status, '');
}

/**
 * HOOKS
 * We use hooks functions for API calls to be able to use the useAuth hook inside of it.
 * It allows us also to use an internal state (handled by useAsyncMemo) for getters which simplifies the component code.
 */

/**
 * useUserProjects
 * retrieve authenticated user's projects list
 * @returns AvailableProjectsModel[] | undefined
 */
export function useUserProjects(): AvailableProjectsModel[] | undefined {
  // auth hook which provides the current authenticated user
  const { authenticatedUser } = useAuth();

  // This method is a GET it retrieves data by querying the API
  // but a hook can not be async it has to be a pure function
  // to handle the query API effect we use useAsyncMemo
  // useAsyncMemo generalizes the internal state management for us
  // useAsyncMemo internally has a generic useState and a useEffect
  // we use useAsyncMemo to lighten our API methods and our component code by providing a ready to consume state
  const projects = useAsyncMemo(async () => {
    // the HTTP call headers needs the Bearer token
    const authHeaders = getAuthHeaders(authenticatedUser);
    if (authenticatedUser) {
      // api calls uses openapi fetch that make sure that method GET, paths `/projects` and params respect API specs
      const res = await api.GET('/projects', {
        ...authHeaders,
        params: {
          header: { username: authenticatedUser.username },
        },
      });

      if (res.data && !res.error)
        // TODO: type API response in Python code and remove the as unknown as AvailableProjectsModel[]
        return values(res.data.projects) as unknown as AvailableProjectsModel[];
      else
        throw new HttpError(
          res.response.status,
          res.error.detail?.map((d) => d.msg).join('; ') || '',
        );
    }
    //TODO notify that user must be logged in
    // this should only happen in a component mounted in a route which is not protected in the router
  }, [authenticatedUser]);

  // here we use the getAsyncMemoData to return only the data or undefined and not the internal status
  return getAsyncMemoData(projects);
}

/**
 * useCreateProject
 * provide a method to POST a new project
 * @returns void
 */
export function useCreateProject() {
  // auth hook
  const { authenticatedUser } = useAuth();

  // POST method hook generates an async function which will do the API call
  // the component using this hook will decide when to use this method  in its lifecycle
  // (typically in a form submit handler)
  // useCallback is a react util which memoizes a function
  // the createProject function will change each time the authenticated user changes
  // therefore the component using this hook will not have to bother handling authentication it's done automatically here
  const createProject = useCallback(
    // this async function needs a ProjectDataModel payload as params
    async (project: ProjectDataModel) => {
      const authHeaders = getAuthHeaders(authenticatedUser);
      if (authenticatedUser) {
        // do the new projects POST call
        const res = await api.POST('/projects/new', {
          ...authHeaders,
          params: { header: { username: authenticatedUser.username } },
          // POST has a body
          body: project,
        });
        if (res.error)
          throw new Error(
            res.error.detail
              ? res.error.detail?.map((d) => d.msg).join('; ')
              : res.error.toString(),
          );
      }
      //TODO: notify
    },
    [authenticatedUser],
  );
  // this POST hook returns a function ready to be used by a component
  return createProject;
}


/**
 * useProject
 * GET project by projectSlug
 * @param projectSlug
 * @returns ProjectModel
 */
export function useProject(projectSlug?: string) {
  // it's a GET data hook. It's using the exact same pattern as useUserProjects

  // 1. get auth
  const { authenticatedUser } = useAuth();

  // 2. use an internal state to store the project thanks to useAsyncMemo
  const project = useAsyncMemo(async () => {
    const authHeaders = getAuthHeaders(authenticatedUser);
    if (authenticatedUser && projectSlug) {
      const res = await api.GET('/projects/{project_slug}', {
        ...authHeaders,
        params: {
          header: { username: authenticatedUser.username },
          path: { project_slug: projectSlug },
        },
      });
      if (res.error)
        throw new Error(
          res.error.detail ? res.error.detail?.map((d) => d.msg).join('; ') : res.error.toString(),
        );
      //return res.data.params;
      return res.data;
    }
    //TODO: notify

    // in this dependencies list we add projectSlug has a different API call will be made if it changes
  }, [authenticatedUser, projectSlug]);

  // 3. make sure to simplify the data returned by discarding the status
  return getAsyncMemoData(project);
}
