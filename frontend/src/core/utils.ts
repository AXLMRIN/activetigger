import { parquetMetadataAsync, parquetRead } from 'hyparquet';
import { fromPairs, zip } from 'lodash';

import { DataType } from '../components/forms/ProjectCreationForm';

/**
 * loadParquetFile
 * parses a parquet file in memory
 * @param file: uploaded file
 * @returns a DataType object storing the data, fieldnames and original filename
 */
export async function loadParquetFile(file: File): Promise<DataType> {
  // since this function is async it must returns a Promise which contains a DataType object

  // read the uploaded file as an arrayBuffer
  const arrayBuffer = await file.arrayBuffer();
  // use th hyparquet library to read the file metadata (which stores the headers)
  const metadata = await parquetMetadataAsync(arrayBuffer);
  // here we have to create a new Promise as the parquetRead function only support the callback syntax
  // The Promise will be return immediately but it will be replaced by what is provided to its resolve function
  // It will be replaced only when the resolve function is called
  // we differ the resolution.
  return new Promise((resolve) =>
    parquetRead({
      metadata,
      file: arrayBuffer,
      // here is the callback which will be called once the file has been loaded
      onComplete: (arrayData) => {
        // extract headers from metadata
        const headers = metadata.schema.slice(1).map((s) => s.name);
        // transforme the data as an array of objects
        const data = arrayData.map((ad) => fromPairs(zip(headers, ad)));
        // resolve the promise with a dataType object
        resolve({ data, headers, filename: file.name });
      },
    }),
  );
}
