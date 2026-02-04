'use client';

import {
  Badge,
  Box,
  Button,
  Card,
  Container,
  Heading,
  HStack,
  SimpleGrid,
  Stack,
  Text,
} from '@chakra-ui/react';

export default function Home() {
  return (
    <Box minH="100vh" bg="gray.50" py={16}>
      <Container maxW="6xl">
        <Stack gap={12}>
          {/* Header */}
          <Stack gap={3} textAlign="center">
            <Heading size="3xl">Chakra UI Showcase</Heading>
            <Text fontSize="xl" color="gray.600">
              A simple demo of various Chakra UI components
            </Text>
          </Stack>

          {/* Buttons */}
          <Stack gap={4}>
            <Heading size="lg">Buttons</Heading>
            <HStack gap={3} flexWrap="wrap">
              <Button colorPalette="blue">Solid</Button>
              <Button variant="outline" colorPalette="blue">
                Outline
              </Button>
              <Button variant="ghost" colorPalette="blue">
                Ghost
              </Button>
              <Button variant="subtle" colorPalette="blue">
                Subtle
              </Button>
              <Button size="sm">Small</Button>
              <Button size="lg">Large</Button>
            </HStack>
          </Stack>

          {/* Badges */}
          <Stack gap={4}>
            <Heading size="lg">Badges</Heading>
            <HStack gap={3} flexWrap="wrap">
              <Badge colorPalette="green">Success</Badge>
              <Badge colorPalette="red">Error</Badge>
              <Badge colorPalette="yellow">Warning</Badge>
              <Badge colorPalette="blue">Info</Badge>
              <Badge variant="outline" colorPalette="purple">
                Outline
              </Badge>
            </HStack>
          </Stack>

          {/* Cards */}
          <Stack gap={4}>
            <Heading size="lg">Cards</Heading>
            <SimpleGrid columns={{ base: 1, md: 3 }} gap={6}>
              <Card.Root>
                <Card.Body>
                  <Heading size="md" mb={2}>
                    Card Title 1
                  </Heading>
                  <Text color="gray.600">
                    This is a simple card with some content inside.
                  </Text>
                </Card.Body>
              </Card.Root>

              <Card.Root>
                <Card.Body>
                  <Heading size="md" mb={2}>
                    Card Title 2
                  </Heading>
                  <Text color="gray.600">
                    Cards can contain any content you want.
                  </Text>
                </Card.Body>
              </Card.Root>

              <Card.Root>
                <Card.Body>
                  <Heading size="md" mb={2}>
                    Card Title 3
                  </Heading>
                  <Text color="gray.600">
                    Responsive grid layout using SimpleGrid.
                  </Text>
                </Card.Body>
              </Card.Root>
            </SimpleGrid>
          </Stack>
        </Stack>
      </Container>
    </Box>
  );
}
