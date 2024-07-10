import { components } from './generated/openapi';

export type UserModel = components['schemas']['UserModel'];

export type ProjectModel = components['schemas']['ProjectModel'];
export type ProjectDataModel = components['schemas']['ProjectDataModel'];
export type AvailableProjectsModel = {
  created_by: string;
  created_at: string;
  parameters: ProjectModel;
};
