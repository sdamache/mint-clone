import React from 'react';
import { Nav } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';

function Sidebar() {
  return (
    <div className="sidebar">
      <Nav className="flex-column">
        <LinkContainer to="/">
          <Nav.Link>Budget Dashboard</Nav.Link>
        </LinkContainer>
        <LinkContainer to="/upload">
          <Nav.Link>Upload CSV</Nav.Link>
        </LinkContainer>
      </Nav>
    </div>
  );
}

export default Sidebar;
