import { HStack, Box, Text } from '@chakra-ui/react';
import { LuBookOpen, LuGraduationCap } from 'react-icons/lu';

export function RoleBadge({ role }: { role: 'student' | 'faculty' }) {
  const Icon = role === 'faculty' ? LuBookOpen : LuGraduationCap;
  const label = role === 'faculty' ? 'Faculty' : 'Student';
  return (
    <HStack
      gap="6px"
      bg="rgba(251,146,60,0.1)"
      border="1.6px solid"
      borderColor="orange.400"
      borderRadius="full"
      px="12px"
      py="4px"
      display="inline-flex"
      flexShrink={0}
    >
      <Box color="orange.400">
        <Icon size={14} />
      </Box>
      <Text fontSize="xs" color="orange.400" fontWeight="medium">
        {label}
      </Text>
    </HStack>
  );
}
