  export interface AppRatings {
    content: Content;
    metadata: Metadata;
  }
  export interface Content {
    ratings?: (RatingsEntity)[] | null;
    start_date: string;
    end_date: string;
  }
  export interface RatingsEntity {
    1: number;
    2: number;
    3: number;
    4: number;
    5: number;
    total: number;
    avg: number;
    store: string;
    date: string;
  }
  export interface Metadata {
    request: Request;
    content: Content1;
  }
  export interface Request {
    path: string;
    store: string;
    params: Params;
    performed_at: string;
  }
  export interface Params {
    start_date: string;
    end_date: string;
    id: string;
    format: string;
  }
  export interface Content1 {
  }
  