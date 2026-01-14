import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

interface NavbarProps {
  dataDate?: string | null;
}

const Navbar: React.FC<NavbarProps> = ({ dataDate }) => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Spotify Export
          {dataDate && (
            <Typography component="span" variant="caption" sx={{ ml: 2, opacity: 0.7 }}>
              (data from {dataDate})
            </Typography>
          )}
        </Typography>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 