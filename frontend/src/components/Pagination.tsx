import React from 'react';
import { Box, Pagination, PaginationItem } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

interface PaginationProps {
  count: number;
  page: number;
  onChange: (event: React.ChangeEvent<unknown>, value: number) => void;
  baseUrl: string;
}

const PaginationComponent: React.FC<PaginationProps> = ({ count, page, onChange, baseUrl }) => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, mb: 4 }}>
      <Pagination
        count={count}
        page={page}
        onChange={onChange}
        color="primary"
        size="large"
        showFirstButton
        showLastButton
        renderItem={(item) => (
          <PaginationItem
            component={RouterLink}
            to={`${baseUrl}${item.page === 1 ? '' : `?page=${item.page}`}`}
            {...item}
          />
        )}
      />
    </Box>
  );
};

export default PaginationComponent; 